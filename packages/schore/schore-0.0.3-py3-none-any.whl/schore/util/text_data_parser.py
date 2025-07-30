from typing import TextIO, Type

from ..type_hints import ScalarT


class TextDataParser:
    """A class to parse text data from a stream."""

    @staticmethod
    def strip_a_line(stream: TextIO) -> str:
        line = stream.readline()
        if not line:
            raise EOFError("Unexpected end of file while reading data.")
        return line.strip()

    # Line as a value

    @staticmethod
    def strip_a_typed_value(stream: TextIO, dtype: Type[ScalarT]) -> ScalarT:
        try:
            return dtype(TextDataParser.strip_a_line(stream))
        except ValueError as e:
            raise ValueError(f"Failed to convert line to {dtype.__name__}: {e}") from e

    # Line as a list

    @staticmethod
    def strip_a_list(stream: TextIO, sep: str | None = None) -> list[str]:
        return TextDataParser.strip_a_line(stream).split(sep=sep)

    @staticmethod
    def strip_a_typed_list(
        stream: TextIO, dtype: Type[ScalarT], sep: str | None = None
    ) -> list[ScalarT]:
        return [dtype(x) for x in TextDataParser.strip_a_list(stream, sep=sep)]

    # Multiple lines as a list of lists

    @staticmethod
    def strip_list_of_a_typed_list(
        stream: TextIO, num_lists: int, dtype: Type[ScalarT], sep: str | None = None
    ) -> list[list[ScalarT]]:
        result: list[list[ScalarT]] = []
        for i in range(num_lists):
            try:
                result.append(TextDataParser.strip_a_typed_list(stream, dtype, sep=sep))
            except EOFError:
                raise EOFError(
                    f"Unexpected end of file while reading {i + 1}-th row"
                    f" among {num_lists} rows of list of type {dtype.__name__}."
                ) from None
        return result
