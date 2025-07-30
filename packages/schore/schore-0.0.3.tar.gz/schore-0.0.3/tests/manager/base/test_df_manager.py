import io

import pandas as pd
import pytest

from src.schore.manager.base.df_manager import DfManager


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
def sample_df_manager():
    """Fixture to provide a sample DfManager instance."""
    df = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    return DfManager(name="SampleDf", df=df)


def test_initialization(sample_df_manager: DfManager):
    """Test the initialization of DfManager."""
    assert sample_df_manager.name == "SampleDf"
    assert sample_df_manager.df.shape == (3, 3)


def test_from_text_stream(sample_text_stream):
    """Test the creation of DfManager from a text stream."""
    df_manager = DfManager.from_text_stream(sample_text_stream, row_count=3)
    assert df_manager.name == "DfManager"
    assert df_manager.df.shape == (3, 3)
    assert df_manager.df.iloc[0, 0] == 1
    assert df_manager.df.iloc[2, 2] == 9


def test_row_count(sample_df_manager: DfManager):
    """Test the row_count method."""
    assert sample_df_manager.row_count() == 3


def test_col_count(sample_df_manager: DfManager):
    """Test the col_count method."""
    assert sample_df_manager.col_count() == 3


def test_to_csv(tmp_path, sample_df_manager: DfManager):
    """Test the to_csv method."""
    output_path = tmp_path / "output.csv"
    sample_df_manager.to_csv(output_path)

    # Verify the file was created
    assert output_path.exists()

    # Verify the contents of the CSV file
    df = pd.read_csv(output_path)

    # Convert column names back to integers if necessary
    df.columns = df.columns.astype(int)

    pd.testing.assert_frame_equal(df, sample_df_manager.df)


def test_repr(sample_df_manager):
    """Test the __repr__ method."""
    assert repr(sample_df_manager) == "DfManager(name='SampleDf', shape=(3, 3))"
