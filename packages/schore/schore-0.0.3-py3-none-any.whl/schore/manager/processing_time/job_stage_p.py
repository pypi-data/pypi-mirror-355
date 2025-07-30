from __future__ import annotations

from typing import Generic, Self, TextIO, Type

import pandas as pd

from ...type_hints import NumericT, ScalarT, numeric_types
from ..base.table_2d_manager import Table2DManager


class JobStageProcessingTimeManager(Table2DManager, Generic[NumericT]):
    """rows for jobs, columns for stages"""

    def __init__(self, name: str, df: pd.DataFrame) -> None:
        super().__init__(name, df)

    @classmethod
    def from_text_stream(
        cls,
        stream: TextIO,
        row_count: int,
        dtype: Type[ScalarT] | None = None,
        sep: str | None = None,
        name: str = "JobStageProcessingTimeManager",
    ) -> Self:
        if dtype is not None:
            if not isinstance(dtype, type):  # Ensure dtype is a type
                raise TypeError(f"Expected dtype to be a type, got {dtype}")
            if dtype is bool:
                raise TypeError("Boolean dtype is not supported for processing times.")
            if dtype not in numeric_types:
                raise TypeError(f"Expected dtype to be a numeric type, got '{dtype}'")
        return super().from_text_stream(stream, row_count, dtype, sep, name)

    def stage_job_2_value_map(
        self, stage_id_list: list[str], job_id_list: list[str]
    ) -> dict[tuple[str, str], NumericT]:
        """
        Create a mapping from stage ID to job ID and value.

        Args:
            stage_id_list (list[str]): List of stage IDs (columns).
            job_id_list (list[str]): List of job IDs (rows).

        Returns:
            dict[tuple[str, str], Numeric]: (Stage ID, Job ID) -> Value.
        """
        assert len(stage_id_list) == self.col_count(), "stage count mismatch"
        assert len(job_id_list) == self.row_count(), "job count mismatch"

        return {
            (stage_id, job_id): self.df.iat[row_idx, col_idx]
            for row_idx, job_id in enumerate(job_id_list)
            for col_idx, stage_id in enumerate(stage_id_list)
        }

    def stage_2_job_2_value_map(
        self, stage_id_list: list[str], job_id_list: list[str]
    ) -> dict[str, dict[str, NumericT]]:
        """
        Create a mapping from stage ID to job ID and value.

        Args:
            stage_id_list (list[str]): List of stage IDs (columns).
            job_id_list (list[str]): List of job IDs (rows).

        Returns:
            dict[str, dict[str, Numeric]]: Stage ID -> Job ID -> Value.
        """
        assert len(stage_id_list) == self.col_count(), "stage count mismatch"
        assert len(job_id_list) == self.row_count(), "job count mismatch"

        return {
            stage_id: {
                job_id: self.df.iat[row_idx, col_idx]
                for row_idx, job_id in enumerate(job_id_list)
            }
            for col_idx, stage_id in enumerate(stage_id_list)
        }

    def job_stage_2_value_map(
        self, job_id_list: list[str], stage_id_list: list[str]
    ) -> dict[tuple[str, str], NumericT]:
        """
        Create a mapping from job ID to stage ID and value.

        Args:
            job_id_list (list[str]): List of job IDs (rows).
            stage_id_list (list[str]): List of stage IDs (columns).

        Returns:
            dict[tuple[str, str], Numeric]: (Job ID, Stage ID) -> Value.
        """
        assert len(job_id_list) == self.row_count(), "job count mismatch"
        assert len(stage_id_list) == self.col_count(), "stage count mismatch"

        return {
            (job_id, stage_id): self.df.iat[row_idx, col_idx]
            for col_idx, stage_id in enumerate(stage_id_list)
            for row_idx, job_id in enumerate(job_id_list)
        }

    def job_2_stage_2_value_map(
        self, job_id_list: list[str], stage_id_list: list[str]
    ) -> dict[str, dict[str, NumericT]]:
        """
        Create a mapping from job ID to stage ID and value.

        Args:
            job_id_list (list[str]): List of job IDs (rows).
            stage_id_list (list[str]): List of stage IDs (columns).

        Returns:
            dict[str, dict[str, Numeric]]: Job ID -> Stage ID -> Value.
        """
        assert len(job_id_list) == self.row_count(), "job count mismatch"
        assert len(stage_id_list) == self.col_count(), "stage count mismatch"

        return {
            job_id: {
                stage_id: self.df.iat[row_idx, col_idx]
                for col_idx, stage_id in enumerate(stage_id_list)
            }
            for row_idx, job_id in enumerate(job_id_list)
        }

    def filter_by_job_indices(
        self, job_index_list: list[int]
    ) -> JobStageProcessingTimeManager[NumericT]:
        """
        Filter the processing times by job indices.

        Args:
            job_index_list (list[int]): List of job indices to filter.

        Returns:
            JobStageProcessingTimeManager: Filtered processing times.
        """
        filtered_df = self.df.iloc[job_index_list, :]
        return JobStageProcessingTimeManager(self.name, filtered_df)
