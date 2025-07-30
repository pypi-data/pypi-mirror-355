import io

import pandas as pd
import pytest

from src.schore import JobStageProcessingTimeManager


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
def sample_processing_time_manager():
    """Fixture to provide a sample JobStageProcessingTimeManager instance."""
    df = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    return JobStageProcessingTimeManager(name="SampleProcessingTime", df=df)


def test_initialization(sample_processing_time_manager: JobStageProcessingTimeManager):
    """Test the initialization of JobStageProcessingTimeManager."""
    assert sample_processing_time_manager.name == "SampleProcessingTime"
    assert sample_processing_time_manager.df.shape == (3, 3)


def test_from_text_stream(sample_text_stream):
    """Test the creation of JobStageProcessingTimeManager from a text stream."""
    manager = JobStageProcessingTimeManager.from_text_stream(
        sample_text_stream, row_count=3
    )
    assert manager.name == "JobStageProcessingTimeManager"
    assert manager.df.shape == (3, 3)
    assert manager.df.iloc[0, 0] == 1
    assert manager.df.iloc[2, 2] == 9


def test_stage_2_job_2_value_map(
    sample_processing_time_manager: JobStageProcessingTimeManager,
):
    """Test the stage_2_job_2_value_map method."""
    stage_ids = ["S1", "S2", "S3"]
    job_ids = ["J1", "J2", "J3"]
    expected_mapping = {
        "S1": {"J1": 1, "J2": 4, "J3": 7},
        "S2": {"J1": 2, "J2": 5, "J3": 8},
        "S3": {"J1": 3, "J2": 6, "J3": 9},
    }
    assert (
        sample_processing_time_manager.stage_2_job_2_value_map(stage_ids, job_ids)
        == expected_mapping
    )


def test_job_2_stage_2_value_map(
    sample_processing_time_manager: JobStageProcessingTimeManager,
):
    """Test the job_2_stage_2_value_map method."""
    job_ids = ["J1", "J2", "J3"]
    stage_ids = ["S1", "S2", "S3"]
    expected_mapping = {
        "J1": {"S1": 1, "S2": 2, "S3": 3},
        "J2": {"S1": 4, "S2": 5, "S3": 6},
        "J3": {"S1": 7, "S2": 8, "S3": 9},
    }
    assert (
        sample_processing_time_manager.job_2_stage_2_value_map(job_ids, stage_ids)
        == expected_mapping
    )


def test_stage_and_job_count_mismatch(
    sample_processing_time_manager: JobStageProcessingTimeManager,
):
    """Test that mismatched stage or job counts raise an AssertionError."""
    with pytest.raises(AssertionError, match="stage count mismatch"):
        sample_processing_time_manager.stage_2_job_2_value_map(
            ["S1", "S2"], ["J1", "J2", "J3"]
        )

    with pytest.raises(AssertionError, match="job count mismatch"):
        sample_processing_time_manager.job_2_stage_2_value_map(
            ["J1", "J2"], ["S1", "S2", "S3"]
        )


def test_from_text_stream_with_float():
    """Test the creation of JobStageProcessingTimeManager with float values."""
    stream = io.StringIO("1.1 2.2 3.3\n4.4 5.5 6.6\n7.7 8.8 9.9\n")
    manager = JobStageProcessingTimeManager.from_text_stream(
        stream, row_count=3, dtype=float
    )
    assert manager.df.shape == (3, 3)
    assert manager.df.iloc[0, 0] == 1.1
    assert manager.df.iloc[2, 2] == 9.9


def test_from_text_stream_invalid_dtype():
    """Test that from_text_stream raises TypeError for invalid dtype."""
    stream = io.StringIO("1 2 3\n4 5 6\n7 8 9\n")
    with pytest.raises(TypeError, match="Expected dtype to be a numeric type"):
        JobStageProcessingTimeManager.from_text_stream(
            stream, row_count=3, dtype=complex
        )
    stream = io.StringIO("True False True\nFalse True False\nTrue True False\n")
    with pytest.raises(
        TypeError, match="Boolean dtype is not supported for processing times."
    ):
        JobStageProcessingTimeManager.from_text_stream(stream, row_count=3, dtype=bool)
    stream = io.StringIO("a b c\nx y z\n1 2 3\n")
    with pytest.raises(TypeError, match="Expected dtype to be a numeric type"):
        JobStageProcessingTimeManager.from_text_stream(stream, row_count=3, dtype=str)
