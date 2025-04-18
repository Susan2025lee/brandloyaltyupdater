"""Module to store LLM prompt templates."""

# Initial, basic prompt for Phase 2 - Summarization Only
# This prompt does not include logic for comparing against a baseline report yet.

BASIC_SUMMARIZATION_PROMPT_TEMPLATE = """
You are an AI assistant tasked with summarizing information relevant to brand loyalty metrics.

**Context:**
I have retrieved the following text excerpts related to the brand loyalty metric: **{metric_name}**.
Each excerpt includes its source filename in the metadata.

```text
{context_excerpts}
```

**Task:**
Please synthesize the key information from the context above specifically regarding the **{metric_name}** metric.
Generate a concise summary paragraph.

**Important:**
- Focus ONLY on the provided context excerpts.
- Extract information directly relevant to **{metric_name}**.
- Clearly cite the source filename(s) from the metadata associated with the information used in your summary (e.g., "According to report1.pdf...", "report2.md mentions...").
- If the context contains no relevant information for the metric, state that clearly.

**Summary:**
"""

# --- Significance Assessment Prompt for Phase 3 ---

SIGNIFICANCE_ASSESSMENT_PROMPT_TEMPLATE = """
You are an AI assistant analyzing updates for a Brand Loyalty Monitoring Report.
Your task is to determine if new information warrants an update to a specific metric section in the report.

**Metric Name:** {metric_name}

**Current Report Section Content:**
```text
{current_section_content}
```

**Newly Retrieved Context:**
Here are relevant excerpts retrieved from new documents. Each includes its source filename.
```text
{retrieved_context}
```

**Instructions:**
1.  **Compare:** Analyze the `Newly Retrieved Context` against the `Current Report Section Content` for the metric **{metric_name}**
2.  **Assess Significance:** Determine if the new information provides a *significant* update (e.g., new data points, trends, substantial changes, contradicting information) compared to the current content. Minor wording changes or information already captured are NOT significant.
3.  **Output:**
    *   **If a significant update IS warranted:** Synthesize the key information from the `Newly Retrieved Context` and integrate it with the `Current Report Section Content` (if appropriate) to generate a *revised* paragraph for the report section. Ensure the revised paragraph is concise, informative, and accurately reflects the *latest* significant information. Cite the source filename(s) from the retrieved context (e.g., "According to report1.pdf...", "Source: report2.md").
    *   **If NO significant update is warranted:** Respond ONLY with the exact phrase: `NO_UPDATE_NEEDED`

**Response:**
"""

# --- Helper function to format context for the prompt --- 
def format_context_for_prompt(retrieved_chunks: list[dict]) -> str:
    """Formats the retrieved chunks into a string suitable for the prompt context.
    Includes metadata (source filename) for citation.
    """
    formatted_string = ""
    for i, chunk in enumerate(retrieved_chunks):
        source = chunk.get('metadata', {}).get('source_filename', 'Unknown Source')
        text = chunk.get('text', '')
        formatted_string += f"--- Excerpt {i+1} (Source: {source}) ---\n"
        formatted_string += text
        formatted_string += "\n\n"
    return formatted_string.strip()


# Example usage (for demonstration)
if __name__ == '__main__':
    # Sample retrieved data
    sample_chunks = [
        {'id': 'docA_0', 'text': 'Customer retention seems high based on recent survey.', 'metadata': {'source_filename': 'survey_q3.pdf'}, 'distance': 0.1},
        {'id': 'docB_5', 'text': 'NPS scores improved slightly in the last quarter.', 'metadata': {'source_filename': 'internal_memo.md'}, 'distance': 0.2},
        {'id': 'docA_1', 'text': 'However, the survey had a small sample size.', 'metadata': {'source_filename': 'survey_q3.pdf'}, 'distance': 0.3}
    ]
    
    metric = "Customer Retention Rate"
    formatted_context = format_context_for_prompt(sample_chunks)
    
    final_prompt = BASIC_SUMMARIZATION_PROMPT_TEMPLATE.format(
        metric_name=metric,
        context_excerpts=formatted_context
    )
    
    print("--- Example Formatted Prompt --- ")
    print(final_prompt) 