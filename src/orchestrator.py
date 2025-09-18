import sys
import os
import shutil
import importlib
from pathlib import Path

sys.path.append('scripts')
sys.path.append('.')

from .ci_agent import ReActAgent
from .llm import get_llm
from .react_runner import run_react_loop
from src.tools import known_actions


def orchestrate_ci_fix(seed_name):
    try:
        workspace_result = create_error_workspace(seed_name)
        if workspace_result["status"] == "fail":
            return workspace_result
        
        workspace_path = Path(workspace_result["data"]["workspace_path"])
        error_info = workspace_result["data"]["error_info"]
        
        agent_result = run_ci_agent(workspace_path)
        if agent_result["status"] == "fail":
            return agent_result
        
        ci_result = check_ci_status(workspace_path)
        
        
        success = (agent_result["status"] == "pass" and ci_result["status"] == "pass")
        
        return {
            "status": "pass" if success else "fail",
            "data": {
                "seed_scenario": seed_name,
                "error_description": error_info.get("description", ""),
                "agent_result": agent_result.get("data", {}).get("result", "unknown"),
                "final_ci_status": ci_result.get("data", {}).get("overall_status", "unknown"),
                "workspace": str(workspace_path)
            },
            "error": None if success else f"Agent result: {agent_result.get('status', 'unknown')}, CI status: {ci_result.get('status', 'unknown')}, Final CI: {ci_result.get('data', {}).get('overall_status', 'unknown')}"
        }
        
    except Exception as e:
        return {
            "status": "fail",
            "error": f"Orchestration failed at main level: {type(e).__name__}: {str(e)}",
            "data": {"seed_scenario": seed_name}
        }


def create_error_workspace(seed_name):
    try:
        workspaces_dir = Path("workspaces")
        workspaces_dir.mkdir(exist_ok=True)
        
        from create_baseline import create_baseline
        temp_baseline = create_baseline("temp_baseline")
        
        workspace_path = workspaces_dir / f"test_{seed_name}"
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
        
        shutil.copytree(temp_baseline, workspace_path)
        shutil.rmtree(temp_baseline)
        
        seed_module = importlib.import_module(f"scenarios.{seed_name}")
        error_info = seed_module.induce_errors(workspace_path)
        
        return {
            "status": "pass",
            "data": {
                "workspace_path": str(workspace_path),
                "error_info": error_info
            }
        }
        
    except Exception as e:
        return {
            "status": "fail",
            "error": f"Workspace creation failed for seed '{seed_name}': {type(e).__name__}: {str(e)}"
        }


def run_ci_agent(workspace_path):
    try:
        llm = get_llm()
        agent = ReActAgent(known_actions, llm)
        result = run_react_loop(agent, str(workspace_path), max_turns=20)
        
        return {
            "status": "pass" if result == "success" else "fail",
            "data": {"result": result}
        }
        
    except Exception as e:
        return {
            "status": "fail",
            "error": f"Agent execution failed in workspace '{workspace_path}': {type(e).__name__}: {str(e)}"
        }


def check_ci_status(workspace_path):
    original_cwd = os.getcwd()
    try:
        import importlib.util
        workspace_path = Path(workspace_path).resolve()
        ci_pipeline_path = workspace_path / "ci_pipeline.py"
        
        
        if not ci_pipeline_path.exists():
            return {
                "status": "fail",
                "error": f"CI pipeline file missing: {ci_pipeline_path} does not exist"
            }
        
        os.chdir(workspace_path)
        
        spec = importlib.util.spec_from_file_location("ci_pipeline", ci_pipeline_path)
        ci_pipeline_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ci_pipeline_module)
        
        pipeline = ci_pipeline_module.CIPipeline(".")
        result = pipeline.run_all_checks()
        
        return {
            "status": "pass" if result["overall_status"] == "pass" else "fail",
            "data": {"overall_status": result["overall_status"]}
        }
        
    except Exception as e:
        return {
            "status": "fail",
            "error": f"CI status check failed in workspace '{workspace_path}': {type(e).__name__}: {str(e)}"
        }
    finally:
        os.chdir(original_cwd)
