import streamlit as st
import sys
import os

# Add src directory to path to allow importing modules from src
# This might need adjustment based on how the app is run
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import necessary functions
from main import run_full_pipeline # Import the actual pipeline function
from report_parser import update_report_section # Import the update function
# from report_parser import read_baseline_report # May be needed

# --- App Configuration ---
st.set_page_config(
    page_title="Brand Loyalty Monitor - Review",
    layout="wide"
)

# --- State Management --- 
# Initialize session state variables if they don't exist
if 'proposed_updates' not in st.session_state:
    st.session_state.proposed_updates = [] # List to hold generated updates
if 'pipeline_run' not in st.session_state:
    st.session_state.pipeline_run = False
if 'pipeline_running' not in st.session_state:
    st.session_state.pipeline_running = False

# --- UI Layout --- 
st.title("Brand Loyalty Monitor - Update Review")

st.markdown("""
This interface shows proposed updates to the Brand Loyalty Baseline Report based on newly processed documents.
Review each proposed update and choose to approve or reject it.
""")

st.divider()

# --- Pipeline Execution --- 

# Placeholder for a button to trigger the pipeline
if st.button("Run Pipeline to Find Updates", disabled=st.session_state.pipeline_running):
    st.session_state.pipeline_running = True
    st.session_state.proposed_updates = [] # Clear previous updates
    st.session_state.pipeline_run = True
    with st.spinner("Processing documents and generating assessments..."):
        try:
            # Call the main pipeline function
            st.session_state.proposed_updates = run_full_pipeline()
            st.success("Pipeline finished.")
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.session_state.proposed_updates = [] # Clear updates on error

    st.session_state.pipeline_running = False
    st.rerun() # Rerun to update the display after pipeline finishes

st.divider()

# --- Display Proposed Updates --- 

st.header("Proposed Updates")

if not st.session_state.pipeline_run:
    st.info("Click 'Run Pipeline to Find Updates' to begin.")
elif not st.session_state.proposed_updates:
    st.success("Pipeline run complete. No significant updates found in the new documents.")
else:
    st.info(f"Found {len(st.session_state.proposed_updates)} potential updates. Please review:")
    
    # Store indices of updates that need removal (after iteration)
    updates_to_remove_indices = []

    for i, update in enumerate(st.session_state.proposed_updates):
        # Skip updates that have already been actioned (approved/rejected)
        if update.get('status') != 'pending':
             continue

        st.subheader(f"Update {i+1}: Metric - {update['metric']}")
        st.markdown(f"**Source:** `{update['source']}`")
        st.markdown("**Proposed Text:**")
        st.text_area("Update Text", value=update['update_text'], key=f"text_{i}", height=150, disabled=True)
        
        col1, col2, col_spacer = st.columns([1, 1, 5])
        with col1:
            if st.button("Approve", key=f"approve_{i}"):
                try:
                    # --- Task 4.7: Actual Report Update Logic --- 
                    success = update_report_section(update['metric'], update['update_text'])
                    if success:
                        st.toast(f"Successfully updated report for {update['metric']}!", icon="✅")
                        update['status'] = 'approved'
                    else:
                        st.toast(f"Failed to update report for {update['metric']}. Check logs.", icon="❌")
                        # Keep status as pending if update fails
                except Exception as e:
                     st.toast(f"Error during report update for {update['metric']}: {e}", icon="❌")
                     st.error(f"Detailed error updating {update['metric']}: {e}") # Show more detail
                st.rerun() # Rerun to refresh UI and potentially remove item
        with col2:
            if st.button("Reject", key=f"reject_{i}"):
                st.toast(f"Rejected update for {update['metric']}.")
                update['status'] = 'rejected'
                st.rerun() # Rerun to refresh UI and potentially remove item

        st.divider()

    # --- Display Actioned Updates (Optional) ---
    st.subheader("Actioned Updates")
    actioned_updates_found = False
    for update in st.session_state.proposed_updates:
         if update.get('status') == 'approved':
             st.success(f"Approved: {update['metric']} (Update action placeholder)")
             actioned_updates_found = True
         elif update.get('status') == 'rejected':
             st.warning(f"Rejected: {update['metric']}")
             actioned_updates_found = True
    if not actioned_updates_found:
        st.caption("No updates actioned yet in this session.")

# Placeholder for a final 'Commit Approved Changes' button if needed
# Or changes could be applied immediately on Approve 