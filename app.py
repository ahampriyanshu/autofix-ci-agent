"""Streamlit App for Autofix CI Agent"""

import streamlit as st
import sys
import os
import io
import threading
import queue
import time
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from pipeline import run


class RealTimeCapture:
    """Capture stdout and stderr in real-time"""
    def __init__(self):
        self.output_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        """Write method for capturing output"""
        if text.strip():  # Only add non-empty lines
            self.output_queue.put(text)
        self.original_stdout.write(text)
        
    def flush(self):
        """Flush method for compatibility"""
        self.original_stdout.flush()
        
    def run_with_capture(self, func, *args, **kwargs):
        """Run function in a separate thread with output capture"""
        def target():
            try:
                # Redirect stdout to our custom capture
                sys.stdout = self
                result = func(*args, **kwargs)
                self.result_queue.put({"success": True, "result": result})
            except Exception as e:
                self.result_queue.put({"success": False, "error": str(e)})
            finally:
                # Restore original stdout
                sys.stdout = self.original_stdout
                self.output_queue.put("__DONE__")  # Signal completion
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        return thread


def main():
    st.title("Autofix CI Agent")
    
    # Custom CSS for green run button and description styling
    st.markdown("""
    <style>
    .stButton > button {
        background-color: #28a745;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        width: 120px;
        height: 35px;
        padding: 0;
        margin-top: 25px;
    }
    .stButton > button:hover {
        background-color: #218838;
        color: white;
    }
    .agent-description {
        color: #888888;
        font-size: 16px;
        margin-bottom: 40px;
    }
    .scenario-description {
        color: #666666;
        font-style: italic;
        font-size: 14px;
        margin-top: 8px;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="agent-description">
    An intelligent CI/CD pipeline autofix agent that automatically detects and resolves common issues in your codebase.
    </div>
    """, unsafe_allow_html=True)
    
    # Get available seed scenarios using absolute path
    app_dir = Path(__file__).parent
    scenarios_dir = app_dir / "scenarios"
    seed_files = list(scenarios_dir.glob("seed_*.py"))
    
    # Create mapping of scenario files to display names
    scenario_display_names = {
        "seed_01_syntax": "Syntax Error - Missing Colon",
        "seed_02_import": "Import Error - Missing Module",
        "seed_03_test": "Test Failure - Wrong Assertion",
        "seed_04_dependency": "Missing Dependency - Numpy",
        "seed_05_yaml": "YAML Config Error - Missing Colon",
        "seed_06_multi": "Multi-Step Chain - Multiple Issues"
    }
    
    # Create mapping of scenario files to descriptions
    scenario_descriptions = {
        "seed_01_syntax": "Tests the agent's ability to detect and fix Python syntax errors, specifically missing colons in function definitions.",
        "seed_02_import": "Evaluates how the agent handles missing import statements when modules are used but not imported.",
        "seed_03_test": "Checks if the agent can identify and correct failing test assertions with wrong expected values.",
        "seed_04_dependency": "Tests the agent's capability to detect missing dependencies and add them to requirements.txt.",
        "seed_05_yaml": "Assesses the agent's ability to fix YAML configuration syntax errors like missing colons.",
        "seed_06_multi": "Comprehensive test with multiple related issues that need to be resolved in sequence."
    }
    
    # Extract scenario names and create display options
    scenario_files = [f.stem for f in sorted(seed_files)]
    scenario_options = [scenario_display_names.get(f, f) for f in scenario_files]
    
    if not scenario_options:
        st.error("No seed scenarios found in the scenarios directory!")
        return
    
    # Create two columns for the selector and button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_display_name = st.selectbox(
            "Select a seed scenario:",
            scenario_options,
            help="Choose which scenario to run the CI autofix agent on"
        )
        
        # Map back from display name to file name
        selected_scenario = None
        for file_name, display_name in scenario_display_names.items():
            if display_name == selected_display_name:
                selected_scenario = file_name
                break
        # Fallback if not found in mapping
        if selected_scenario is None:
            selected_scenario = selected_display_name
    
    with col2:
        run_button = st.button("Run", type="primary")
    
    # Display scenario description if available
    if selected_scenario and selected_scenario in scenario_descriptions:
        description = scenario_descriptions[selected_scenario]
        st.markdown(f'<div class="scenario-description">{description}</div>', unsafe_allow_html=True)

    # Run the agent when button is clicked
    if run_button and selected_scenario:
        st.write("---")
        st.subheader(f"Running {selected_display_name}...")
        
        # Create real-time output display
        status_text = st.empty()
        output_container = st.container()
        output_text = output_container.empty()
        
        # Initialize real-time capture
        capture = RealTimeCapture()
        
        status_text.info("🔄 Starting CI autofix agent...")
        
        # Start the pipeline in a separate thread
        thread = capture.run_with_capture(run, selected_scenario)
        
        # Real-time output display
        output_lines = []
        
        while thread.is_alive() or not capture.output_queue.empty():
            try:
                # Get new output with a short timeout
                line = capture.output_queue.get(timeout=0.1)
                if line == "__DONE__":
                    break
                    
                output_lines.append(line.rstrip())
                
                # Update the display with latest output (show last 50 lines)
                display_lines = output_lines[-50:] if len(output_lines) > 50 else output_lines
                output_text.code('\n'.join(display_lines), language="text")
                
            except queue.Empty:
                # No new output, just wait a bit
                time.sleep(0.1)
                continue
        
        # Wait for thread to complete and get result
        thread.join(timeout=1)
        
        # Get the final result
        try:
            result_data = capture.result_queue.get_nowait()
        except queue.Empty:
            result_data = {"success": False, "error": "Pipeline execution timeout or error"}
        
        # Update status based on result
        pipeline_failed = False
        
        if result_data["success"]:
            pipeline_result = result_data.get("result", {})
            
            # Check if pipeline result indicates success or failure
            if isinstance(pipeline_result, dict):
                pipeline_status = pipeline_result.get("status", "unknown")
                
                if pipeline_status == "pass":
                    status_text.success("Pipeline execution completed successfully! All issues fixed.")
                elif pipeline_status == "fail":
                    pipeline_failed = True
                    error_msg = pipeline_result.get("error", "CI pipeline failed")
                    status_text.error(f"Pipeline failed: {error_msg}")
                    
                    # Display additional error details if available
                    if "data" in pipeline_result and pipeline_result["data"]:
                        st.error("**Error Details:**")
                        st.code(str(pipeline_result["data"]), language="text")
                else:
                    status_text.warning(f"Pipeline completed with unknown status: {pipeline_status}")
            else:
                # Fallback for non-dict results
                status_text.success("Pipeline execution completed!")
        else:
            # Pipeline execution itself failed (exception occurred)
            pipeline_failed = True
            error_msg = result_data.get('error', 'Unknown error')
            status_text.error(f"Pipeline execution failed: {error_msg}")
            
            # Display the error in a more prominent way
            st.error("**Execution Error:**")
            st.code(error_msg, language="text")
        
        # If pipeline failed, hide the output and show expandable full output section
        if pipeline_failed:
            # Clear the output container
            output_text.empty()
            
            # Add expandable section for full pipeline output
            with st.expander("🔍 View Full Pipeline Output", expanded=False):
                st.code('\n'.join(output_lines), language="text")
        # If pipeline succeeded, keep the output visible as before


if __name__ == "__main__":
    main()
