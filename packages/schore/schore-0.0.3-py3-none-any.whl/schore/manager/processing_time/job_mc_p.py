from __future__ import annotations

from typing import Generic, Self, TextIO, Type

import pandas as pd

from ...type_hints import NumericT, ScalarT, numeric_types
from ..base.table_2d_manager import Table2DManager


class JobMachineProcessingTimeManager(Table2DManager, Generic[NumericT]):
    """rows for jobs, columns for machines"""

    def __init__(self, name: str, df: pd.DataFrame) -> None:
        super().__init__(name, df)

    @classmethod
    def from_text_stream(
        cls,
        stream: TextIO,
        row_count: int,
        dtype: Type[ScalarT] | None = None,
        sep: str | None = None,
        name: str = "JobMachineProcessingTimeManager",
    ) -> Self:
        if dtype is not None:
            if not isinstance(dtype, type):  # Ensure dtype is a type
                raise TypeError(f"Expected dtype to be a type, got {dtype}")
            if dtype is bool:
                raise TypeError("Boolean dtype is not supported for processing times.")
            if dtype not in numeric_types:
                raise TypeError(f"Expected dtype to be a numeric type, got '{dtype}'")
        return super().from_text_stream(stream, row_count, dtype, sep, name)

    def machine_2_job_2_value_map(
        self, mc_id_list: list[str], job_id_list: list[str]
    ) -> dict[str, dict[str, NumericT]]:
        """
        Create a mapping from machine ID to job ID and value.

        Args:
            mc_id_list (list[str]): List of machine IDs (columns).
            job_id_list (list[str]): List of job IDs (rows).

        Returns:
            dict[str, dict[str, Numeric]]: Machine ID -> Job ID -> Value.
        """
        assert len(mc_id_list) == self.col_count(), "machine count mismatch"
        assert len(job_id_list) == self.row_count(), "job count mismatch"

        return {
            mc_id: {
                job_id: self.df.iat[row_idx, col_idx]
                for row_idx, job_id in enumerate(job_id_list)
            }
            for col_idx, mc_id in enumerate(mc_id_list)
        }

    def machine_job_2_value_map(
        self, mc_id_list: list[str], job_id_list: list[str]
    ) -> dict[tuple[str, str], NumericT]:
        """
        Create a mapping from machine ID to job ID and value.

        Args:
            mc_id_list (list[str]): List of machine IDs (columns).
            job_id_list (list[str]): List of job IDs (rows).

        Returns:
            dict[tuple[str, str], Numeric]: (Machine ID, Job ID) -> Value.
        """
        assert len(mc_id_list) == self.col_count(), "machine count mismatch"
        assert len(job_id_list) == self.row_count(), "job count mismatch"

        return {
            (mc_id, job_id): self.df.iat[row_idx, col_idx]
            for row_idx, job_id in enumerate(job_id_list)
            for col_idx, mc_id in enumerate(mc_id_list)
        }

    def job_2_eligible_mc_list_map(
        self, job_id_list: list[str], mc_id_list: list[str]
    ) -> dict[str, list[str]]:
        """
        Create a mapping from job ID to eligible machine IDs.

        Args:
            job_id_list (list[str]): List of job IDs (rows).
            mc_id_list (list[str]): List of machine IDs (columns).

        Returns:
            dict[str, list[str]]: Job ID -> List of eligible machine IDs.
        """
        assert len(mc_id_list) == self.col_count(), "machine count mismatch"
        assert len(job_id_list) == self.row_count(), "job count mismatch"

        return {
            job_id: [
                mc_id
                for col_idx, mc_id in enumerate(mc_id_list)
                if self.df.iat[row_idx, col_idx] > 0
            ]
            for row_idx, job_id in enumerate(job_id_list)
        }

    def filter_by_job_indices(
        self, job_index_list: list[int]
    ) -> JobMachineProcessingTimeManager:
        """
        Filter the DataFrame by job indices.

        Args:
            job_index_list (list[int]): List of job indices to filter.

        Returns:
            JobMachineProcessingTimeManager: New instance with filtered data.
        """
        filtered_df = self.df.iloc[job_index_list, :]
        return JobMachineProcessingTimeManager(name=self.name, df=filtered_df)
