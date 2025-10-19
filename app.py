import streamlit as st
import sys
import threading
import queue
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from pipeline import run


class RealTimeCapture:
    def __init__(self):
        self.output_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, text):
        if text.strip():
            self.output_queue.put(text)
        self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()

    def run_with_capture(self, func, *args, **kwargs):
        def target():
            try:
                sys.stdout = self
                result = func(*args, **kwargs)
                self.result_queue.put({"success": True, "result": result})
            except Exception as e:
                self.result_queue.put({"success": False, "error": str(e)})
            finally:
                sys.stdout = self.original_stdout
                self.output_queue.put("__DONE__")

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        return thread


def main():
    st.set_page_config(
        page_title="Autofix CI Agent",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items=None,
    )

    st.title("Autofix CI Agent")

    st.markdown(
        """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="agent-description">
    An intelligent CI/CD pipeline autofix agent that automatically detects and resolves common issues in your codebase.
    </div>
    """,
        unsafe_allow_html=True,
    )

    app_dir = Path(__file__).parent
    scenarios_dir = app_dir / "scenarios"
    seed_files = list(scenarios_dir.glob("seed_*.py"))

    scenario_display_names = {
        "seed_syntax": "Syntax Error - Missing Colon",
        "seed_import": "Import Error - Missing Module",
        "seed_lint": "Linting Error - PEP8 Violations",
        "seed_multi": "Multiple Syntax Errors",
    }

    scenario_descriptions = {
        "seed_syntax": "Tests the agent's ability to detect and fix Python syntax errors, specifically missing colons in function definitions.",
        "seed_import": "Evaluates how the agent handles missing import statements when modules are used but not imported.",
        "seed_lint": "Assesses the agent's capability to fix PEP8 linting errors such as missing blank lines (E302).",
        "seed_multi": "Comprehensive test with multiple syntax errors in the same file that need to be resolved sequentially.",
    }

    scenario_files = [f.stem for f in sorted(seed_files)]
    scenario_options = [scenario_display_names.get(f, f) for f in scenario_files]

    if not scenario_options:
        st.error("No seed scenarios found in the scenarios directory!")
        return

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_display_name = st.selectbox(
            "Select a seed scenario:",
            scenario_options,
            help="Choose which scenario to run the CI autofix agent on",
        )

        selected_scenario = None
        for file_name, display_name in scenario_display_names.items():
            if display_name == selected_display_name:
                selected_scenario = file_name
                break
        if selected_scenario is None:
            selected_scenario = selected_display_name

    with col2:
        run_button = st.button("Run", type="primary")

    if selected_scenario and selected_scenario in scenario_descriptions:
        description = scenario_descriptions[selected_scenario]
        st.markdown(
            f'<div class="scenario-description">{description}</div>',
            unsafe_allow_html=True,
        )

    if run_button and selected_scenario:
        st.write("---")
        st.subheader(f"Running {selected_display_name}...")

        status_text = st.empty()
        output_container = st.container()
        output_text = output_container.empty()

        capture = RealTimeCapture()

        status_text.info("🔄 Starting CI autofix agent...")

        thread = capture.run_with_capture(run, selected_scenario)

        output_lines = []

        while thread.is_alive() or not capture.output_queue.empty():
            try:
                line = capture.output_queue.get(timeout=0.1)
                if line == "__DONE__":
                    break

                output_lines.append(line.rstrip())

                display_lines = (
                    output_lines[-50:] if len(output_lines) > 50 else output_lines
                )
                output_text.code("\n".join(display_lines), language="text")

            except queue.Empty:
                time.sleep(0.1)
                continue

        thread.join(timeout=1)

        try:
            result_data = capture.result_queue.get_nowait()
        except queue.Empty:
            result_data = {
                "success": False,
                "error": "Pipeline execution timeout or error",
            }

        pipeline_failed = False

        if result_data["success"]:
            pipeline_result = result_data.get("result", {})

            if isinstance(pipeline_result, dict):
                pipeline_status = pipeline_result.get("status", "unknown")

                if pipeline_status == "pass":
                    status_text.success(
                        "Pipeline execution completed successfully! All issues fixed."
                    )
                elif pipeline_status == "fail":
                    pipeline_failed = True
                    error_msg = pipeline_result.get("error", "CI pipeline failed")
                    status_text.error(f"Pipeline failed: {error_msg}")

                    if "data" in pipeline_result and pipeline_result["data"]:
                        st.error("**Error Details:**")
                        st.code(str(pipeline_result["data"]), language="text")
                else:
                    status_text.warning(
                        f"Pipeline completed with unknown status: {pipeline_status}"
                    )
            else:
                status_text.success("Pipeline execution completed!")
        else:
            pipeline_failed = True
            error_msg = result_data.get("error", "Unknown error")
            status_text.error(f"Pipeline execution failed: {error_msg}")

            st.error("**Execution Error:**")
            st.code(error_msg, language="text")

        if pipeline_failed:
            output_text.empty()

            with st.expander("🔍 View Full Pipeline Output", expanded=False):
                st.code("\n".join(output_lines), language="text")


if __name__ == "__main__":
    main()
