import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os
from typing import List, Dict, Any

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Module to test
import generate
from prompts import SIGNIFICANCE_ASSESSMENT_PROMPT_TEMPLATE
from core.llm_interface import LLMInterface # Needed for mocking

# --- Fixtures --- 

@pytest.fixture
def sample_retrieved_chunks_gen() -> List[Dict[str, Any]]: # Renamed fixture
    """Provides sample retrieved chunk data for generation tests."""
    return [
        {'id': 'docC_1', 'text': 'Significant drop in Q4.', 'metadata': {'source_filename': 'q4_report.pdf'}, 'distance': 0.05},
        {'id': 'docD_2', 'text': 'Competitor action impacting numbers.', 'metadata': {'source_filename': 'market_watch.md'}, 'distance': 0.1}
    ]

@pytest.fixture
def mock_llm_interface_assess() -> MagicMock: # Renamed fixture
    """Provides a mocked LLMInterface instance for assessment tests."""
    mock = MagicMock(spec=LLMInterface)
    mock.model_name = "mock-assessment-model"
    # Default mock response (can be overridden in tests)
    mock.generate_response.return_value = "Generated update based on new context."
    return mock

@pytest.fixture
def mock_report_parser():
    """Provides patches for report_parser functions."""
    with patch('generate.read_baseline_report') as mock_read, \
         patch('generate.extract_metric_section') as mock_extract:
        # Default mock behavior (can be overridden in tests)
        mock_read.return_value = "# Report\n\n## Metric One\nExisting content.\n"
        mock_extract.return_value = "Existing content."
        yield mock_read, mock_extract

# --- Test Cases for generate_assessment_for_metric --- 

def test_generate_assessment_success_update(sample_retrieved_chunks_gen, mock_llm_interface_assess, mock_report_parser):
    """Test successful assessment resulting in an update."""
    metric = "Metric One"
    mock_read, mock_extract = mock_report_parser
    expected_update = "Generated update based on new context."
    mock_llm_interface_assess.generate_response.return_value = expected_update

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_llm_interface_assess
    )

    assert result == expected_update
    mock_read.assert_called_once()
    mock_extract.assert_called_once_with(mock_read.return_value, metric)
    mock_llm_interface_assess.generate_response.assert_called_once()
    call_args, call_kwargs = mock_llm_interface_assess.generate_response.call_args
    prompt = call_kwargs.get('prompt')
    assert metric in prompt
    assert "Existing content." in prompt # From mock_extract
    assert "Significant drop in Q4." in prompt # From chunks
    assert call_kwargs.get('temperature') == 0.3

def test_generate_assessment_success_no_update(sample_retrieved_chunks_gen, mock_llm_interface_assess, mock_report_parser):
    """Test successful assessment resulting in NO_UPDATE_NEEDED."""
    metric = "Metric One"
    mock_llm_interface_assess.generate_response.return_value = generate.NO_UPDATE_MARKER

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_llm_interface_assess
    )

    assert result == generate.NO_UPDATE_MARKER
    mock_llm_interface_assess.generate_response.assert_called_once()

def test_generate_assessment_llm_fails(sample_retrieved_chunks_gen, mock_llm_interface_assess, mock_report_parser):
    """Test when the LLM call returns None."""
    metric = "Metric One"
    mock_llm_interface_assess.generate_response.return_value = None

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_llm_interface_assess
    )

    assert result is None
    mock_llm_interface_assess.generate_response.assert_called_once()

def test_generate_assessment_no_chunks(mock_llm_interface_assess, mock_report_parser):
    """Test assessment when retrieved_chunks is empty."""
    metric = "Metric One"
    mock_read, mock_extract = mock_report_parser

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=[],
        llm_interface=mock_llm_interface_assess
    )

    assert result == generate.NO_UPDATE_MARKER
    mock_read.assert_not_called()
    mock_extract.assert_not_called()
    mock_llm_interface_assess.generate_response.assert_not_called()

def test_generate_assessment_report_not_found(sample_retrieved_chunks_gen, mock_llm_interface_assess, mock_report_parser):
    """Test assessment when baseline report is not found."""
    metric = "Metric One"
    mock_read, mock_extract = mock_report_parser
    mock_read.side_effect = FileNotFoundError("File not found")

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_llm_interface_assess
    )

    assert result is None
    mock_read.assert_called_once()
    mock_extract.assert_not_called()
    mock_llm_interface_assess.generate_response.assert_not_called()

def test_generate_assessment_report_read_error(sample_retrieved_chunks_gen, mock_llm_interface_assess, mock_report_parser):
    """Test assessment when baseline report reading causes IOError."""
    metric = "Metric One"
    mock_read, mock_extract = mock_report_parser
    mock_read.side_effect = IOError("Read error")

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_llm_interface_assess
    )

    assert result is None
    mock_read.assert_called_once()
    mock_extract.assert_not_called()
    mock_llm_interface_assess.generate_response.assert_not_called()

def test_generate_assessment_section_not_found(sample_retrieved_chunks_gen, mock_llm_interface_assess, mock_report_parser):
    """Test assessment when metric section is not found in the report."""
    metric = "Metric Two"
    mock_read, mock_extract = mock_report_parser
    mock_extract.return_value = None # Simulate section not found
    expected_update = "Generated update based on new context (no existing section)."
    mock_llm_interface_assess.generate_response.return_value = expected_update

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_llm_interface_assess
    )

    assert result == expected_update
    mock_read.assert_called_once()
    mock_extract.assert_called_once_with(mock_read.return_value, metric)
    mock_llm_interface_assess.generate_response.assert_called_once()
    # Check that current_section_content was empty in the prompt
    call_args, call_kwargs = mock_llm_interface_assess.generate_response.call_args
    prompt = call_kwargs.get('prompt')
    assert "**Current Report Section Content:**" in prompt
    assert "```text\n\n```" in prompt # Check for the empty code block structure


@patch('generate.LLMInterface') # Patch LLMInterface where it's imported in generate
def test_generate_assessment_llm_init_fails(mock_llm_init, sample_retrieved_chunks_gen, mock_report_parser):
    """Test assessment when LLMInterface initialization fails (if called)."""
    metric = "Metric One"
    mock_llm_init.side_effect = ValueError("Init failed")

    # Call with llm_interface=None to trigger the initialization path
    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=None
    )

    assert result is None
    mock_llm_init.assert_called_once() # Verify init was attempted

def test_generate_assessment_interface_no_model(sample_retrieved_chunks_gen, mock_report_parser):
    """Test providing an interface without a model configured."""
    metric = "Metric One"
    mock_interface = MagicMock(spec=LLMInterface)
    mock_interface.model_name = None # No model configured

    result = generate.generate_assessment_for_metric(
        metric_name=metric,
        retrieved_chunks=sample_retrieved_chunks_gen,
        llm_interface=mock_interface
    )

    assert result is None
    mock_interface.generate_response.assert_not_called() 