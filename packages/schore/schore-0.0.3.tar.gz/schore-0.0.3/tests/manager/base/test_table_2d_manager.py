import io

import pandas as pd
import pytest

from src.schore.manager.base.table_2d_manager import Table2DManager


@pytest.fixture
def sample_text_stream():
    """Fixture to provide a sample text stream."""
    data = """\
1 2 3
4 5 6
7 8 9
"""
    return io.StringIO(data)


@pytest.fixture
def sample_table_2d_manager():
    """Fixture to provide a sample Table2DManager instance."""
    df = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    return Table2DManager(name="SampleTable2D", df=df)


def test_initialization(sample_table_2d_manager: Table2DManager):
    """Test the initialization of Table2DManager."""
    assert sample_table_2d_manager.name == "SampleTable2D"
    assert sample_table_2d_manager.df.shape == (3, 3)


def test_from_text_stream(sample_text_stream):
    """Test the creation of Table2DManager from a text stream."""
    table_manager = Table2DManager.from_text_stream(sample_text_stream, row_count=3)
    assert table_manager.name == "Table2DManager"
    assert table_manager.df.shape == (3, 3)
    assert table_manager.df.iloc[0, 0] == 1
    assert table_manager.df.iloc[2, 2] == 9


def test_col_idx_2_row_idx_2_value_map(sample_table_2d_manager: Table2DManager):
    """Test the col_idx_2_row_idx_2_value_map method."""
    expected_mapping = {
        0: {0: 1, 1: 4, 2: 7},
        1: {0: 2, 1: 5, 2: 8},
        2: {0: 3, 1: 6, 2: 9},
    }
    assert sample_table_2d_manager.col_idx_2_row_idx_2_value_map() == expected_mapping


def test_repr(sample_table_2d_manager: Table2DManager):
    """Test the __repr__ method."""
    assert (
        repr(sample_table_2d_manager)
        == "Table2DManager(name='SampleTable2D', shape=(3, 3))"
    )
