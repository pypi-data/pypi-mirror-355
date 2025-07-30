import io

import pytest

from src.schore.util import TextDataParser


def test_strip_a_line():
    """Test the strip_a_line method."""
    stream = io.StringIO("  Hello, World!  \n")
    result = TextDataParser.strip_a_line(stream)
    assert result == "Hello, World!"


def test_strip_a_line_eof():
    """Test that strip_a_line raises EOFError on empty stream."""
    stream = io.StringIO("")
    with pytest.raises(EOFError, match="Unexpected end of file while reading data."):
        TextDataParser.strip_a_line(stream)


def test_strip_a_typed_value():
    """Test the strip_a_typed_value method."""
    stream = io.StringIO("  42  \n")
    result = TextDataParser.strip_a_typed_value(stream, int)
    assert result == 42


def test_strip_a_typed_value_invalid():
    """Test that strip_a_typed_value raises ValueError on invalid conversion."""
    stream = io.StringIO("not_a_number\n")
    with pytest.raises(ValueError, match="Failed to convert line to int:"):
        TextDataParser.strip_a_typed_value(stream, int)


def test_strip_a_list():
    """Test the strip_a_list method."""
    stream = io.StringIO("1,2,3\n")
    result = TextDataParser.strip_a_list(stream, sep=",")
    assert result == ["1", "2", "3"]


def test_strip_a_typed_list():
    """Test the strip_a_typed_list method."""
    stream = io.StringIO("1,2,3\n")
    result = TextDataParser.strip_a_typed_list(stream, int, sep=",")
    assert result == [1, 2, 3]


def test_strip_list_of_a_typed_list():
    """Test the strip_list_of_a_typed_list method."""
    stream = io.StringIO("1,2,3\n4,5,6\n7,8,9\n")
    result = TextDataParser.strip_list_of_a_typed_list(stream, 3, int, sep=",")
    assert result == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def test_strip_list_of_a_typed_list_eof():
    """Test that strip_list_of_a_typed_list raises EOFError on insufficient lines."""
    stream = io.StringIO("1,2,3\n4,5,6\n")
    with pytest.raises(
        EOFError,
        match="Unexpected end of file while reading 3-th row"
        " among 3 rows of list of type int.",
    ):
        TextDataParser.strip_list_of_a_typed_list(stream, 3, int, sep=",")
        TextDataParser.strip_list_of_a_typed_list(stream, 3, int, sep=",")
