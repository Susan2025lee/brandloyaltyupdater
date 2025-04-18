import sys
import os
from typing import Optional, List, Dict, Any

# Ensure src directory is in path - REMOVED
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary components
# Use relative imports assuming execution context allows
try:
    from .core.llm_interface import LLMInterface
    from .prompts import (
        BASIC_SUMMARIZATION_PROMPT_TEMPLATE, # Keep for potential fallback/other uses
        SIGNIFICANCE_ASSESSMENT_PROMPT_TEMPLATE,
        format_context_for_prompt
    )
    from .report_parser import read_baseline_report, extract_metric_section
except ImportError:
    # Fallback for potential direct script execution (less ideal)
    # This assumes src is in PYTHONPATH or script is run from root
    print("Warning: Using fallback imports for generate.py. Relative imports preferred.")
    from core.llm_interface import LLMInterface
    from prompts import (
        BASIC_SUMMARIZATION_PROMPT_TEMPLATE,
        SIGNIFICANCE_ASSESSMENT_PROMPT_TEMPLATE,
        format_context_for_prompt
    )
    from report_parser import read_baseline_report, extract_metric_section

# Define the specific string indicating no update is needed
NO_UPDATE_MARKER = "NO_UPDATE_NEEDED"

def generate_assessment_for_metric(
    metric_name: str,
    retrieved_chunks: List[Dict[str, Any]],
    llm_interface: Optional[LLMInterface] = None,
    prompt_template: str = SIGNIFICANCE_ASSESSMENT_PROMPT_TEMPLATE
) -> Optional[str]:
    """Generates a significance assessment for a metric based on retrieved chunks
    and the current baseline report context.

    Reads the baseline report, extracts the relevant section, and uses an LLM
    to compare new information (retrieved_chunks) against the current content.
    Determines if an update is significant and either returns the updated text
    or a specific marker (NO_UPDATE_MARKER) if no update is needed.

    Args:
        metric_name: The name of the metric being assessed.
        retrieved_chunks: A list of dictionaries, where each dict represents a
                          retrieved text chunk with its content and metadata.
        llm_interface: An optional pre-initialized LLMInterface instance.
                       If None, a default one will be created.
        prompt_template: The prompt template to use for the LLM call.
                         Defaults to SIGNIFICANCE_ASSESSMENT_PROMPT_TEMPLATE.

    Returns:
        - The updated text for the metric section if a significant change is found.
        - The specific string NO_UPDATE_MARKER if no significant change is needed.
        - None if an error occurs during the process.
    """
    if not retrieved_chunks:
        print(f"No chunks provided for metric '{metric_name}'. Skipping assessment.")
        # If no new info, no update is needed by definition for this function's purpose
        return NO_UPDATE_MARKER

    # 1. Read Baseline Report Content
    try:
        report_content = read_baseline_report()
    except FileNotFoundError:
        print("Error: Baseline report not found. Cannot perform assessment.")
        return None
    except IOError as e:
        print(f"Error reading baseline report: {e}")
        return None

    # 2. Extract Current Section Content
    current_section_content = extract_metric_section(report_content, metric_name)
    if current_section_content is None:
        print(f"Warning: Metric section '{metric_name}' not found in baseline report. Treating as empty.")
        current_section_content = "" # Default to empty if not found

    # 3. Initialize LLM Interface if not provided
    if not llm_interface:
        try:
            print("Initializing LLMInterface for generation...")
            llm_interface = LLMInterface()
        except Exception as e:
            print(f"Error initializing LLMInterface: {e}")
            return None

    if not llm_interface.model_name:
        print("Error: LLMInterface provided has no model configured.")
        return None

    # 4. Format the context for the prompt
    formatted_retrieved_context = format_context_for_prompt(retrieved_chunks)

    # 5. Create the final prompt
    final_prompt = prompt_template.format(
        metric_name=metric_name,
        current_section_content=current_section_content,
        retrieved_context=formatted_retrieved_context
    )

    print(f"\nGenerating assessment for metric: '{metric_name}' using {llm_interface.model_name}...")

    # 6. Use LLMInterface to generate the response
    response = llm_interface.generate_response(
        prompt=final_prompt,
        temperature=0.3 # Slightly lower temp for more deterministic assessment
    )

    if response:
        # 7. Check for NO_UPDATE_MARKER
        response_stripped = response.strip()
        if response_stripped == NO_UPDATE_MARKER:
            print(f"Assessment for '{metric_name}': No significant update needed.")
            return NO_UPDATE_MARKER
        else:
            print(f"Assessment for '{metric_name}': Update generated.")
            return response_stripped # Return the generated update
    else:
        print(f"Failed to generate assessment from LLM for metric '{metric_name}'.")
        return None


# --- Example Usage (Updated) --- 

if __name__ == '__main__':
    # Ensure necessary environment variables (e.g., OPENAI_API_KEY, DEFAULT_LLM_MODEL_KEY)
    # and baseline_report.md are set up.

    # Sample retrieved data
    sample_chunks_update = [
        {'id': 'docC_1', 'text': 'Recent analysis shows a 15% drop in customer retention in Q4.', 'metadata': {'source_filename': 'q4_report.pdf'}, 'distance': 0.05},
        {'id': 'docD_2', 'text': 'Competitor X launched a new loyalty program, impacting our numbers. (Source: market_watch.md)', 'metadata': {'source_filename': 'market_watch.md'}, 'distance': 0.1}
    ]
    sample_chunks_no_update = [
        {'id': 'docE_0', 'text': 'General brand sentiment remains positive.', 'metadata': {'source_filename': 'social_media_scan.txt'}, 'distance': 0.4}
    ]

    # --- !!! IMPORTANT !!! --- 
    # For this example to run meaningfully, you MUST:
    # 1. Have a baseline report at data/core_files/baseline_report.md
    # 2. Ensure that report contains a section for the metric being tested (e.g., ## Customer Retention Rate)
    # --- !!!!!!!!!!!!!!!!! --- 

    metric_to_test = "Customer Retention Rate" # CHANGE THIS if your report uses a different metric name

    print(f"--- Testing Significance Assessment for: {metric_to_test} --- ")

    print("\n--- Case 1: Expecting an update ---")
    try:
        # Use a shared LLM interface instance for efficiency if running multiple tests
        shared_llm = LLMInterface() 
        generated_assessment_update = generate_assessment_for_metric(
            metric_to_test, 
            sample_chunks_update,
            llm_interface=shared_llm
        )

        if generated_assessment_update == NO_UPDATE_MARKER:
            print("\nResult: NO_UPDATE_NEEDED")
        elif generated_assessment_update:
            print("\n--- Generated Update --- ")
            print(generated_assessment_update)
        else:
            print("\nAssessment generation failed.")

    except Exception as e:
        print(f"\nAn error occurred during Case 1: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Case 2: Expecting NO update ---")
    try:
        # Reuse the LLM interface
        generated_assessment_no_update = generate_assessment_for_metric(
            metric_to_test, 
            sample_chunks_no_update,
            llm_interface=shared_llm # Reuse the interface
        )

        if generated_assessment_no_update == NO_UPDATE_MARKER:
            print("\nResult: NO_UPDATE_NEEDED")
        elif generated_assessment_no_update:
            print("\n--- Unexpected Update Generated --- ")
            print(generated_assessment_no_update)
        else:
            print("\nAssessment generation failed.")

    except Exception as e:
        print(f"\nAn error occurred during Case 2: {e}")
        import traceback
        traceback.print_exc() 