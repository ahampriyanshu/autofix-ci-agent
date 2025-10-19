import subprocess
import sys
from pathlib import Path


def run_ci_pipeline():
    """Run complete CI pipeline and return status"""
    try:
        workspace_path = Path.cwd()
        ci_script = workspace_path / "ci_pipeline.py"

        if not ci_script.exists():
            result = subprocess.run(
                ["python3", "-m", "pytest", "-v"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return {"action": "run_ci_pipeline", "status": "pass"}
            else:
                return {
                    "action": "run_ci_pipeline",
                    "status": "fail",
                    "error": f"Test failures:\n{result.stdout}\n{result.stderr}",
                }

        result = subprocess.run(
            ["python3", "ci_pipeline.py", "."],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return {"action": "run_ci_pipeline", "status": "pass"}
        else:
            return {
                "action": "run_ci_pipeline",
                "status": "fail",
                "error": f"CI pipeline failed\n{result.stdout}",
            }

    except subprocess.TimeoutExpired:
        return {
            "action": "run_ci_pipeline",
            "status": "fail",
            "error": "CI pipeline timed out",
        }
    except Exception as e:
        return {
            "action": "run_ci_pipeline",
            "status": "fail",
            "error": f"CI error - {str(e)}",
        }
