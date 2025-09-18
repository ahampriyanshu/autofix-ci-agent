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
    
    # Custom CSS for green run button
    st.markdown("""
    <style>
    .stButton > button {
        background-color: #28a745;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #218838;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    **An intelligent CI/CD pipeline autofix agent that automatically detects and resolves common issues in your codebase.**
    """)
    
    # Get available seed scenarios
    scenarios_dir = Path("scenarios")
    seed_files = list(scenarios_dir.glob("seed_*.py"))
    
    # Extract scenario names (without .py extension)
    scenario_options = [f.stem for f in sorted(seed_files)]
    
    if not scenario_options:
        st.error("No seed scenarios found in the scenarios directory!")
        return
    
    # Create two columns for the selector and button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_scenario = st.selectbox(
            "Select a seed scenario:",
            scenario_options,
            help="Choose which scenario to run the CI autofix agent on"
        )
    
    with col2:
        st.write("")  # Add some spacing
        st.write("")  # Add some spacing
        run_button = st.button("Run", type="primary")
    
    # Display scenario description if available
    if selected_scenario:
        scenario_path = scenarios_dir / f"{selected_scenario}.py"
        try:
            with open(scenario_path, 'r') as f:
                content = f.read()
                # Try to extract docstring or comments for description
                lines = content.split('\n')
                description_lines = []
                for line in lines[:10]:  # Check first 10 lines
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        # Found docstring start
                        if line.count('"""') == 2 or line.count("'''") == 2:
                            # Single line docstring
                            description_lines.append(line.strip().strip('"""').strip("'''").strip())
                            break
                    elif line.strip().startswith('#'):
                        # Comment line
                        description_lines.append(line.strip().lstrip('#').strip())
                
                if description_lines:
                    st.info(f"**Scenario Description:** {' '.join(description_lines[:3])}")
        except Exception:
            pass  # Ignore errors reading scenario files
    
    # Run the agent when button is clicked
    if run_button and selected_scenario:
        st.write("---")
        st.subheader(f"🚀 Running {selected_scenario}...")
        
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
        
        # Update status
        if result_data["success"]:
            status_text.success("✅ Pipeline execution completed!")
        else:
            status_text.error(f"❌ Pipeline execution failed: {result_data.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
