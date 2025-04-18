"""Report parser module to extract information from the baseline report."""

import os
import re
from typing import Optional

from config import BASELINE_REPORT_PATH


def read_baseline_report() -> str:
    """Reads the entire content of the baseline report file.

    Returns:
        The content of the baseline report as a string.

    Raises:
        FileNotFoundError: If the baseline report file does not exist.
        IOError: If there is an error reading the file.
    """
    if not os.path.exists(BASELINE_REPORT_PATH):
        raise FileNotFoundError(f"Baseline report not found at: {BASELINE_REPORT_PATH}")

    try:
        with open(BASELINE_REPORT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except IOError as e:
        print(f"Error reading baseline report {BASELINE_REPORT_PATH}: {e}")
        raise # Re-raise the IOError


def extract_metric_section(report_content: str, metric_name: str) -> Optional[str]:
    """Extracts the text content for a specific metric section from the report.

    Searches for Markdown headings (## or ###) that match the metric name,
    potentially including numbering like 'III.1. metric_name'. Extracts
    content until the next heading of the same or higher level (#, ##, ###)
    or the end of the report.

    Args:
        report_content: The full Markdown content of the report.
        metric_name: The name of the metric to find (case-sensitive).

    Returns:
        The extracted text content of the section, stripped of leading/trailing
        whitespace, or None if the metric section is not found.
    """
    if not metric_name or not report_content:
        return None

    # Escape metric name for regex and allow optional numbering/punctuation before it
    escaped_metric_name = re.escape(metric_name)
    # Updated pattern: Looks for H3 (###), optional space, a capital letter, a dot, space, then the metric name.
    # Uses re.IGNORECASE for the metric name itself.
    start_pattern = re.compile(
        r"^(###)\s*[A-Z]\.\s+" + escaped_metric_name + r"\s*\n",
        re.MULTILINE | re.IGNORECASE
    )

    match = start_pattern.search(report_content)

    if not match:
        print(f"Metric section '{metric_name}' not found.")
        return None

    # Found the start, determine the heading level (len of ###)
    heading_level = len(match.group(1))
    start_index = match.end()

    # Pattern to find the *next* heading of the same or higher level
    # Looks for '#', '##', ..., up to the found level
    next_heading_pattern = re.compile(r"^#{1," + str(heading_level) + r"}\s", re.MULTILINE)

    # Search for the next heading *after* the matched section start
    next_match = next_heading_pattern.search(report_content, start_index)

    if next_match:
        end_index = next_match.start()
    else:
        # No subsequent heading found, take content until the end
        end_index = len(report_content)

    # Extract and clean the content
    section_content = report_content[start_index:end_index].strip()

    return section_content


def update_report_section(metric_name: str, new_content: str) -> bool:
    """Updates a specific metric section in the baseline report file.

    Reads the report, finds the section using regex matching the heading,
    replaces the content of that section with the new content, and writes
    the modified report back to the file.

    Args:
        metric_name: The name of the metric section to update.
        new_content: The new text content for the section.

    Returns:
        True if the update was successful, False otherwise.
    """
    if not metric_name:
        print("Error: Metric name cannot be empty for update.")
        return False

    try:
        report_content = read_baseline_report()
    except (FileNotFoundError, IOError) as e:
        print(f"Error accessing baseline report for update: {e}")
        return False

    # Reuse regex logic from extract_metric_section to find the boundaries
    escaped_metric_name = re.escape(metric_name)
    # Updated pattern: Looks for H3 (###), optional space, a capital letter, a dot, space, then the metric name.
    # Uses re.IGNORECASE for the metric name itself.
    start_pattern = re.compile(
        r"^(###)\s*[A-Z]\.\s+" + escaped_metric_name + r"\s*\n",
        re.MULTILINE | re.IGNORECASE
    )
    match = start_pattern.search(report_content)

    if not match:
        print(f"Error: Metric section heading '### [A-Z]. {metric_name}' not found in report. Cannot update.")
        return False

    heading_level = len(match.group(1)) # Will always be 3 for ###
    section_start_index = match.end() # Start of the content, right after the heading line
    heading_start_index = match.start() # Start of the heading line itself

    # Find the end of the section (start of the next heading or end of file)
    next_heading_pattern = re.compile(r"^#{1," + str(heading_level) + r"}\s", re.MULTILINE)
    next_match = next_heading_pattern.search(report_content, section_start_index)

    if next_match:
        section_end_index = next_match.start()
    else:
        section_end_index = len(report_content)

    # Ensure new content ends with a newline if it's not empty
    # and preserve spacing between sections
    formatted_new_content = new_content.strip()
    if formatted_new_content:
        formatted_new_content += "\n\n" # Add two newlines for spacing before next section
    else:
        formatted_new_content = "\n" # Ensure at least one newline after heading if content is empty

    # Construct the new report content
    updated_report_content = (
        report_content[:section_start_index] + # Content before the section
        formatted_new_content +              # New section content
        report_content[section_end_index:]  # Content after the section
    )

    # Write the updated content back to the file
    try:
        with open(BASELINE_REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_report_content)
        print(f"Successfully updated metric section '{metric_name}' in {BASELINE_REPORT_PATH}")
        return True
    except IOError as e:
        print(f"Error writing updated baseline report {BASELINE_REPORT_PATH}: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during file write: {e}")
        return False