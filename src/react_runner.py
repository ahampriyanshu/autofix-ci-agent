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
        try:
            initial_result = execute_tool_in_workspace(agent.workspace_path, "run_ci_pipeline", "")
            if initial_result is None:
                print("❌ Error: Failed to execute initial CI pipeline check")
                return "error"
                
            observation_data = {
                "observation": f"Initial CI status: {initial_result}",
                "ci_status": "pass" if isinstance(initial_result, dict) and initial_result.get("status") == "pass" else "fail",
                "next_action_needed": True
            }
        except Exception as e:
            print(f"❌ Error during initial CI check: {str(e)}")
            return "error"
        
        # Check if already passing
        if observation_data["ci_status"] == "pass":
            print("✅ CI already passing!")
            return "success"
        
        print(f"❌ CI failing, starting fix process...")
        
        # ReAct loop: Reason → Act → Observe
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        for turn in range(max_turns):
            print(f"\n--- Turn {turn + 1}/{max_turns} ---")
            
            try:
                # REASON: Analyze current situation
                try:
                    reasoning = agent.reason(observation_data["observation"])
                    if reasoning is None:
                        print("❌ Error: Agent reasoning returned None")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                            return "error"
                        continue
                        
                    if "error" in reasoning:
                        print(f"Reason: Error - {reasoning['error']}")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                            return "error"
                        continue
                        
                    # Display reasoning
                    print(f"Reason: \"{reasoning.get('reasoning', 'No reasoning provided')}\"")
                    
                except Exception as e:
                    print(f"❌ Error during reasoning step: {str(e)}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                        return "error"
                    continue
                
                # ACT: Execute chosen action
                try:
                    action_result = agent.act(reasoning)
                    if action_result is None:
                        print("❌ Error: Agent action returned None")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                            return "error"
                        continue
                        
                    if action_result.get("status") == "error":
                        print(f"Act: Error - {action_result.get('error', 'Unknown error')}")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                            return "error"
                        continue
                    
                    # Display action
                    action = action_result.get('action', 'unknown')
                    input_param = action_result.get('input', '')
                    if input_param:
                        print(f"Act: {action}(\"{input_param}\")")
                    else:
                        print(f"Act: {action}()")
                        
                except Exception as e:
                    print(f"❌ Error during action step: {str(e)}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                        return "error"
                    continue
                
                # OBSERVE: Interpret results
                try:
                    observation_data = agent.observe(action_result)
                    if observation_data is None:
                        print("❌ Error: Agent observation returned None")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                            return "error"
                        continue
                        
                    print(f"Observe: \"{observation_data.get('observation', 'No observation')}\"")
                    
                    # Reset consecutive errors on successful step
                    consecutive_errors = 0
                    
                except Exception as e:
                    print(f"❌ Error during observation step: {str(e)}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                        return "error"
                    continue
                
                # Check if CI now passes
                if observation_data.get("ci_status") == "pass":
                    print("🎉 SUCCESS! All CI checks now pass!")
                    return "success"
                
                # If no more actions needed, break
                if not observation_data.get("next_action_needed", True):
                    break
                    
            except Exception as e:
                print(f"❌ Unexpected error in ReAct loop turn {turn + 1}: {str(e)}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"❌ Too many consecutive errors ({consecutive_errors}), aborting")
                    return "error"
                continue
                
        print(f"⏰ Max turns ({max_turns}) reached")
        return "error"
        
    except Exception as e:
        print(f"❌ Critical error in ReAct runner: {str(e)}")
        return "error"
    finally:
        try:
            os.chdir(original_cwd)
        except Exception as e:
            print(f"⚠️ Warning: Failed to restore original directory: {str(e)}")
