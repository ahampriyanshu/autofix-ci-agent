"""CI AutoFix Agent - USER IMPLEMENTS THIS FILE"""

from pathlib import Path
from .helpers import execute_tool_in_workspace

class ReActAgent:
    def __init__(self, tools, llm):
        self.tools = tools  # Pre-built tools provided
        self.llm = llm
        self.workspace_path = None
        
    def reason(self, observation):
        """
        USER IMPLEMENTS: LLM reasoning step
        
        This method should analyze the current observation and decide what action to take next.
        It should use the LLM with the system prompt to generate reasoning and select appropriate tools.
        
        Args:
            observation (str): Current state/results from previous action (e.g., "CI failed with syntax error")
            
        Returns:
            dict: {
                "reasoning": str,  # Explanation of what the agent is thinking
                "tool_call": {
                    "tool": str,   # Name of tool to use (e.g., "analyze_file")
                    "input": str   # Parameters for the tool (e.g., "calculator.py")
                }
            }
        """
        raise NotImplementedError("User must implement the reason() method")
    
    def act(self, reasoning):
        """
        USER IMPLEMENTS: Tool selection & execution
        
        This method should extract the tool and input from reasoning, then execute the chosen tool.
        It should handle errors gracefully and return structured results.
        
        Args:
            reasoning (dict): Output from reason() step containing tool_call information
            
        Returns:
            dict: {
                "status": str,     # "success" or "error"
                "action": str,     # Name of tool that was executed
                "input": str,      # Input parameters used
                "result": dict,    # Result from tool execution
                "error": str       # Error message if status is "error"
            }
        """
        raise NotImplementedError("User must implement the act() method")
    
    def observe(self, action_result):
        """
        USER IMPLEMENTS: Result interpretation
        
        This method should interpret the results from tool execution and determine the next steps.
        It should analyze whether CI is now passing and if more actions are needed.
        
        Args:
            action_result (dict): Output from act() step containing tool execution results
            
        Returns:
            dict: {
                "observation": str,           # Human-readable summary of what happened
                "ci_status": str,            # "pass", "fail", or "unknown" 
                "next_action_needed": bool   # Whether agent should continue or stop
            }
        """
        raise NotImplementedError("User must implement the observe() method")
