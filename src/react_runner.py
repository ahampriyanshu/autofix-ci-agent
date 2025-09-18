"""ReAct Loop Runner - PROVIDED BY FRAMEWORK"""

import os
from pathlib import Path
from .helpers import execute_tool_in_workspace


def run_react_loop(agent, workspace_path, max_turns=10):
    """
    Main ReAct loop implementation - PROVIDED BY FRAMEWORK
    
    Args:
        agent: The ReActAgent instance
        workspace_path: Path to workspace to fix
        max_turns: Maximum iterations
        
    Returns:
        str: "success" or "error"
    """
    agent.workspace_path = str(Path(workspace_path).absolute())
    
    # No tracking needed - just return simple status
    
    # Change to workspace directory for tool execution
    original_cwd = os.getcwd()
    try:
        os.chdir(workspace_path)
        print(f"🚀 Starting ReAct CI Agent on {workspace_path}")
        
        # Initial observation - check CI status
        initial_result = execute_tool_in_workspace(agent.workspace_path, "run_ci_pipeline", "")
        observation_data = {
            "observation": f"Initial CI status: {initial_result}",
            "ci_status": "pass" if isinstance(initial_result, dict) and initial_result.get("status") == "pass" else "fail",
            "next_action_needed": True
        }
        
        # Check if already passing
        if observation_data["ci_status"] == "pass":
            print("✅ CI already passing!")
            return "success"
        
        print(f"❌ CI failing, starting fix process...")
        
        # ReAct loop: Reason → Act → Observe
        for turn in range(max_turns):
            print(f"\n--- Turn {turn + 1}/{max_turns} ---")
            
            # REASON: Analyze current situation
            reasoning = agent.reason(observation_data["observation"])
            
            if "error" in reasoning:
                print(f"Reason: Error - {reasoning['error']}")
                continue
            
            # Display reasoning
            print(f"Reason: \"{reasoning.get('reasoning', 'No reasoning provided')}\"")
            
            # ACT: Execute chosen action
            action_result = agent.act(reasoning)
            
            if action_result.get("status") == "error":
                print(f"Act: Error - {action_result.get('error', 'Unknown error')}")
                continue
            
            # Display action
            action = action_result.get('action', 'unknown')
            input_param = action_result.get('input', '')
            if input_param:
                print(f"Act: {action}(\"{input_param}\")")
            else:
                print(f"Act: {action}()")
            
            # OBSERVE: Interpret results
            observation_data = agent.observe(action_result)
            print(f"Observe: \"{observation_data.get('observation', 'No observation')}\"")
            
            # Check if CI now passes
            if observation_data.get("ci_status") == "pass":
                print("🎉 SUCCESS! All CI checks now pass!")
                return "success"
            
            # If no more actions needed, break
            if not observation_data.get("next_action_needed", True):
                break
                
        print(f"⏰ Max turns ({max_turns}) reached")
        return "error"
    finally:
        os.chdir(original_cwd)
