from __future__ import annotations

from typing import TextIO

from .. import JobStageProcessingTimeManager
from ..util import TextDataParser


class HybridFlowShopProblem:
    """
    Represents a hybrid flow shop problem instance with multiple jobs and stages,
    where each stage may have multiple parallel machines.

    This class assumes all machines at a given stage are eligible for any operation at that stage.
    """  # noqa: E501

    name: str
    """Name of the problem instance."""

    _job_id_list: list[str]
    """A list of job IDs."""
    _stage_id_list: list[str]
    """A list of stage IDs."""
    _stage_2_machines_map: dict[str, list[str]]
    """Mapping from stage IDs to lists of machine IDs at that stage."""
    p_manager: JobStageProcessingTimeManager[int]
    """Manager for processing times of jobs at each stage."""

    def __init__(
        self,
        name: str,
        job_id_list: list[str],
        stage_id_list: list[str],
        stage_2_machines_map: dict[str, list[str]],
        p_manager: JobStageProcessingTimeManager,
    ):
        self.name = name
        self._job_id_list = job_id_list
        self._stage_id_list = stage_id_list
        self._stage_2_machines_map = stage_2_machines_map  # e.g., [2, 3, 2]
        self.p_manager = p_manager

    @property
    def job_id_list(self) -> list[str]:
        """Get list of job IDs."""
        return self._job_id_list.copy()

    @property
    def stage_id_list(self) -> list[str]:
        """Get list of stage IDs."""
        return self._stage_id_list.copy()

    @property
    def stage_2_machines_map(self) -> dict[str, list[str]]:
        """Get mapping from stage IDs to lists of machine IDs."""
        return self._stage_2_machines_map.copy()

    @property
    def job_count(self) -> int:
        return len(self._job_id_list)

    @property
    def stage_count(self) -> int:
        return len(self._stage_id_list)

    @property
    def machine_count_per_stage(self) -> list[int]:
        """List of the number of parallel machines at each stage."""
        return [
            len(self._stage_2_machines_map[stage_id])
            for stage_id in self._stage_id_list
        ]

    def __repr__(self):
        return (
            f"HybridFlowShopProblem(job_count={self.job_count},"
            f" stage_count={self.stage_count})"
        )

    @classmethod
    def from_pra_data(cls, name: str, stream: TextIO) -> "HybridFlowShopProblem":
        """
        Parse hybrid flow shop problem instance from a text stream in PRA-style format.

        Expected format:
            <job_count>
            <stage_count>
            <machine_count_per_stage>  # space-separated list
            <processing_time_row_0>
            <processing_time_row_1>
            ...
            <processing_time_row_n-1>

        Args:
            name (str): Name of the problem instance.
            stream (TextIO): Input stream (e.g., open file or StringIO) containing instance data.

        Returns:
            HybridFlowShopProblem: Parsed problem instance.
        """  # noqa: E501
        job_count = TextDataParser.strip_a_typed_value(stream, int)
        stage_count = TextDataParser.strip_a_typed_value(stream, int)
        machine_count_per_stage = TextDataParser.strip_a_typed_list(stream, int)

        cls._validate_machine_count_per_stage(stage_count, machine_count_per_stage)

        # Generate a list of job IDs with zero-padded numbers.
        num_digits = len(str(job_count - 1))
        job_id_list = [f"j{str(j).zfill(num_digits)}" for j in range(job_count)]

        # Generate a list of stage IDs with zero-padded numbers.
        num_digits = len(str(stage_count - 1))
        stage_id_list = [f"i{str(s).zfill(num_digits)}" for s in range(stage_count)]

        # Generate a mapping from stage IDs to lists of machine IDs.
        stage_2_machines_map: dict[str, list[str]] = {}
        for stage_idx, stage_id in enumerate(stage_id_list):
            num_digits = len(str(machine_count_per_stage[stage_idx] - 1))
            machine_ids = [
                f"{stage_id}_{str(m).zfill(num_digits)}"
                for m in range(machine_count_per_stage[stage_idx])
            ]
            stage_2_machines_map[stage_id] = machine_ids

        processing_times = JobStageProcessingTimeManager.from_text_stream(
            stream, job_count, dtype=int
        )

        cls._validate_processing_times(job_count, stage_count, processing_times)

        return cls(
            name, job_id_list, stage_id_list, stage_2_machines_map, processing_times
        )

    @staticmethod
    def _validate_machine_count_per_stage(
        stage_count: int, machine_count_per_stage: list[int]
    ):
        if len(machine_count_per_stage) != stage_count:
            raise ValueError(
                f"Stage count mismatch; stage_count={stage_count};"
                f" by machine_count_per_stage={len(machine_count_per_stage)}"
            )

    @staticmethod
    def _validate_processing_times(
        job_count: int,
        stage_count: int,
        processing_times: JobStageProcessingTimeManager,
    ):
        if processing_times.df.isnull().values.any():
            raise ValueError("Null value exists in the processing time data.")
        if processing_times.row_count() != job_count:
            raise ValueError(
                f"Job count mismatch; expected {job_count},"
                f" got {processing_times.row_count()}."
            )
        if processing_times.col_count() != stage_count:
            raise ValueError(
                f"Stage count mismatch; expected {stage_count},"
                f" got {processing_times.col_count()}."
            )

    def create_instance_of_job_subset(
        self, job_id_sublist: list[str]
    ) -> HybridFlowShopProblem:
        """Create a new instance of HybridFlowShopProblem with a subset of jobs.

        Args:
            job_id_sublist (list[str]): List of job IDs to include in the new instance.

        Raises:
            ValueError: If the job subset contains invalid job IDs.

        Returns:
            HybridFlowShopProblem: New problem instance with the specified job subset.
        """

        if not set(job_id_sublist).issubset(self.job_id_list):
            raise ValueError("Job subset contains invalid job IDs.")

        job_index_list = [self._job_id_list.index(job_id) for job_id in job_id_sublist]
        new_processing_times = self.p_manager.filter_by_job_indices(job_index_list)

        return HybridFlowShopProblem(
            self.name,
            job_id_sublist,
            self.stage_id_list,
            self.stage_2_machines_map,
            new_processing_times,
        )
