from typing import Hashable, Self, TextIO, Type

import pandas as pd

from ...type_hints import ScalarT
from .df_manager import DfManager


class Table2DManager(DfManager):
    """A class to manage a 2D table represented as a DataFrame."""

    def __init__(self, name: str, df: pd.DataFrame) -> None:
        super().__init__(name, df)

    def __repr__(self) -> str:
        return f"Table2DManager(name='{self.name}', shape={self.df.shape})"

    @classmethod
    def from_text_stream(
        cls,
        stream: TextIO,
        row_count: int,
        dtype: Type[ScalarT] | None = None,
        sep: str | None = None,
        name: str = "Table2DManager",
    ) -> Self:
        return super().from_text_stream(stream, row_count, dtype, sep, name)

    def col_idx_2_row_idx_2_value_map(self) -> dict[int, dict[Hashable, ScalarT]]:
        """
        Create a mapping from column index to row index and value.

        Returns:
            dict: Column index -> row index -> value.
        """
        return {
            col_idx: col_series.to_dict()
            for col_idx, (_, col_series) in enumerate(self.df.items())
        }

    def col_name_2_row_idx_2_value_map(self) -> dict[Hashable, dict[Hashable, ScalarT]]:
        """
        Create a mapping from column name to row index and value.

        Returns:
            dict: Column name -> row index -> value.
        """
        return {
            col_name: col_series.to_dict() for col_name, col_series in self.df.items()
        }
