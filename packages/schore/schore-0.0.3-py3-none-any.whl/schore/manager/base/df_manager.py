from pathlib import Path
from typing import Self, TextIO, Type, cast

import pandas as pd

from ...type_hints import ScalarT, scalar_types
from ...util.text_data_parser import TextDataParser


class DfManager:
    """A class to manage a DataFrame."""

    def __init__(self, name: str, df: pd.DataFrame) -> None:
        self.name = name
        self.df = df

    def __repr__(self) -> str:
        return f"DfManager(name='{self.name}', shape={self.df.shape})"

    @classmethod
    def from_text_stream(
        cls,
        stream: TextIO,
        row_count: int,
        dtype: Type[ScalarT] | None = None,
        sep: str | None = None,
        name: str = "DfManager",
    ) -> Self:
        """Create a DfManager instance from a text stream.

        Args:
            stream (TextIO): Input text stream.
            row_count (int): Number of rows to read from the stream.
            dtype (Type[Scalar], optional): Data type to cast the values to. Defaults to int.
            sep (str | None, optional): Column separator. Defaults to any whitespace.
            name (str): The name of the table. Defaults to "DfManager".

        Returns:
            DfManager: instance with parsed table.
        """
        _dtype = dtype or int
        if _dtype not in scalar_types:
            raise TypeError(f"Expected dtype to be a scalar type, got '{_dtype}'")

        rows: list[list[ScalarT]] = TextDataParser.strip_list_of_a_typed_list(
            stream, row_count, cast(Type[ScalarT], _dtype), sep=sep
        )
        df = pd.DataFrame(rows)
        return cls(name, df)

    def row_count(self) -> int:
        return len(self.df)

    def col_count(self) -> int:
        return len(self.df.columns)

    def to_csv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(path, index=False)
