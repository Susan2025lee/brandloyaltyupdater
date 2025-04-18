import pytest
from unittest.mock import patch, mock_open
import sys
import os
from pathlib import Path
import builtins # Import builtins for patching open

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Module to test
import report_parser
from config import BASELINE_REPORT_PATH # Import the actual path variable

# --- Fixtures --- 

@pytest.fixture
def sample_report_content() -> str:
    """Provides sample Markdown content for testing section extraction."""
    return """
# Report Title

Some intro text.

## Metric One

Content for metric one.
It spans multiple lines.

## Metric Two: Detailed Name

Content for metric two.

### Sub-section under Two

More details.

## Metric Three

Content for metric three.

# Overall Summary

Final thoughts.
"""

@pytest.fixture
def sample_report_content_numbered() -> str:
    """Provides sample Markdown content with numbered headings."""
    return """
# Report Title

Some intro text.

### III.1 Metric One

Content for metric one (numbered).

### III.2 Metric Two

Content for metric two (numbered).

## IV Summary Section

More text.
"""

# --- Test Cases --- 

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data="Mock report content")
def test_read_baseline_report_success(mock_file_open, mock_exists):
    """Test successfully reading the baseline report."""
    mock_exists.return_value = True # Simulate file exists
    
    content = report_parser.read_baseline_report()
    
    assert content == "Mock report content"
    mock_exists.assert_called_once_with(BASELINE_REPORT_PATH)
    # Check that open was called with the correct path from config and encoding
    mock_file_open.assert_called_once_with(BASELINE_REPORT_PATH, 'r', encoding='utf-8')

@patch('os.path.exists')
def test_read_baseline_report_not_found(mock_exists):
    """Test reading when the baseline report file doesn't exist."""
    mock_exists.return_value = False # Simulate file doesn't exist
    
    with pytest.raises(FileNotFoundError) as excinfo:
        report_parser.read_baseline_report()

    assert str(BASELINE_REPORT_PATH) in str(excinfo.value)
    mock_exists.assert_called_once_with(BASELINE_REPORT_PATH)

@patch('os.path.exists')
@patch('builtins.open', side_effect=IOError("Permission denied"))
def test_read_baseline_report_read_error(mock_file_open, mock_exists):
    """Test reading when an IOError occurs during open/read."""
    mock_exists.return_value = True # Simulate file exists
    
    with pytest.raises(IOError) as excinfo:
        report_parser.read_baseline_report()

    assert "Permission denied" in str(excinfo.value)
    mock_exists.assert_called_once_with(BASELINE_REPORT_PATH)
    mock_file_open.assert_called_once_with(BASELINE_REPORT_PATH, 'r', encoding='utf-8')

# -- Tests for extract_metric_section --

def test_extract_metric_section_found(sample_report_content):
    """Test extracting a standard metric section."""
    section = report_parser.extract_metric_section(sample_report_content, "Metric One")
    expected = "Content for metric one.\nIt spans multiple lines."
    assert section == expected

def test_extract_metric_section_found_detailed_name(sample_report_content):
    """Test extracting a metric with a colon in the name."""
    section = report_parser.extract_metric_section(sample_report_content, "Metric Two: Detailed Name")
    expected = "Content for metric two.\n\n### Sub-section under Two\n\nMore details."
    assert section == expected

def test_extract_metric_section_last_section(sample_report_content):
    """Test extracting the last metric section before a higher-level heading."""
    section = report_parser.extract_metric_section(sample_report_content, "Metric Three")
    expected = "Content for metric three."
    assert section == expected

def test_extract_metric_section_numbered(sample_report_content_numbered):
    """Test extracting a metric section with numbering."""
    section = report_parser.extract_metric_section(sample_report_content_numbered, "Metric One")
    expected = "Content for metric one (numbered)."
    assert section == expected

def test_extract_metric_section_numbered_last(sample_report_content_numbered):
    """Test extracting the last numbered metric section."""
    section = report_parser.extract_metric_section(sample_report_content_numbered, "Metric Two")
    expected = "Content for metric two (numbered)."
    assert section == expected

def test_extract_metric_section_not_found(sample_report_content):
    """Test extracting a metric that doesn't exist."""
    section = report_parser.extract_metric_section(sample_report_content, "NonExistent Metric")
    assert section is None

def test_extract_metric_section_empty_content():
    """Test extraction with empty report content."""
    section = report_parser.extract_metric_section("", "Metric One")
    assert section is None

def test_extract_metric_section_empty_name(sample_report_content):
    """Test extraction with empty metric name."""
    section = report_parser.extract_metric_section(sample_report_content, "")
    assert section is None

def test_extract_metric_section_empty_section(sample_report_content):
    """Test extraction where heading exists but section is empty."""
    content_with_empty = sample_report_content + "\n## Empty Metric\n\n## Next Metric"
    section = report_parser.extract_metric_section(content_with_empty, "Empty Metric")
    assert section == "" 