"""Test evaluation for ReAct Agent - PROVIDED"""

import pytest
import os
import json
import shutil
from pathlib import Path
from src.ci_agent import ReActAgent
from src.llm import get_llm
from src.tools import known_actions
from src.react_runner import run_react_loop
from src.helpers import execute_tool_in_workspace
from scripts.create_baseline import create_baseline
from judge.llm_judge import judge_reasoning_output, judge_action_output, judge_observation_output, judge_full_scenario


class TestReActAgent:
    
    def setup_method(self):
        """Setup test environment"""
        self.llm = get_llm()
        self.tools = known_actions
        self.agent = ReActAgent(self.tools, self.llm)
        
        # Define expected efficiency thresholds for each scenario
        self.scenario_thresholds = {
            "seed_01_syntax": 3,      # Simple syntax fix
            "seed_02_import": 6,      # Import + lint fixes
            "seed_03_test": 2,        # Test assertion fix
            "seed_04_dependency": 4,  # Dependency + lint fixes
            "seed_05_yaml": 3,        # YAML syntax fix
            "seed_06_multi": 8        # Multi-step complex scenario
        }
    
    # Utility Functions
    
    def judge_react_step(self, step_type, step_output, context):
        """
        Judge a single ReAct step using LLM judge
        
        Args:
            step_type: 'reason', 'act', or 'observe'
            step_output: The output from the ReAct method
            context: Context dict with scenario info
            
        Returns:
            Judge evaluation dict with pass, score, feedback, reasons
        """
        if step_type == 'reason':
            return judge_reasoning_output(step_output, context, self.llm)
        elif step_type == 'act':
            return judge_action_output(step_output, context, self.llm)
        elif step_type == 'observe':
            return judge_observation_output(step_output, context, self.llm)
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    def judge_scenario_execution(self, scenario_name, workspace_path, max_turns=10):
        """
        Execute a scenario and capture all steps for LLM judging
        
        Args:
            scenario_name: Name of the scenario
            workspace_path: Path to workspace
            max_turns: Maximum turns allowed
            
        Returns:
            Dict with scenario data and judge evaluation
        """
        # Set up agent workspace
        self.agent.workspace_path = workspace_path
        
        # Get initial observation
        initial_ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        current_observation = f"Initial CI status: {initial_ci_result}"
        
        steps = []
        
        # Check if already passing
        if isinstance(initial_ci_result, dict) and initial_ci_result.get("status") == "pass":
            scenario_data = {
                'scenario_name': scenario_name,
                'steps': [],
                'final_result': 'success',
                'total_turns': 0
            }
            return {
                'scenario_data': scenario_data,
                'judge_evaluation': judge_full_scenario(scenario_data, self.llm)
            }
        
        # Execute ReAct loop with step capture
        for turn in range(max_turns):
            # REASON step
            reasoning = self.agent.reason(current_observation)
            
            if "error" in reasoning:
                break
            
            # ACT step
            action_result = self.agent.act(reasoning)
            
            if action_result.get("status") == "error":
                break
            
            # OBSERVE step
            observation_data = self.agent.observe(action_result)
            
            # Capture this step
            step_data = {
                'turn': turn + 1,
                'initial_observation': current_observation,
                'reasoning': reasoning,
                'action_result': action_result,
                'observation': observation_data
            }
            steps.append(step_data)
            
            # Update observation for next turn
            current_observation = observation_data.get('observation', '')
            
            # Check if CI now passes
            if observation_data.get("ci_status") == "pass":
                scenario_data = {
                    'scenario_name': scenario_name,
                    'steps': steps,
                    'final_result': 'success',
                    'total_turns': turn + 1
                }
                return {
                    'scenario_data': scenario_data,
                    'judge_evaluation': judge_full_scenario(scenario_data, self.llm)
                }
            
            # Check if no more actions needed
            if not observation_data.get("next_action_needed", True):
                break
        
        scenario_data = {
            'scenario_name': scenario_name,
            'steps': steps,
            'final_result': 'error',
            'total_turns': len(steps)
        }
        
        return {
            'scenario_data': scenario_data,
            'judge_evaluation': judge_full_scenario(scenario_data, self.llm)
        }
    
    def assert_judge_quality(self, evaluation, min_score=60):
        """
        Assert that judge evaluation meets quality standards
        
        Args:
            evaluation: Judge evaluation dict
            min_score: Minimum acceptable score (0-100)
        """
        assert evaluation['pass'], f"Judge failed: {evaluation['feedback']}"
        assert evaluation['score'] >= min_score, f"Score too low: {evaluation['score']}/100. Feedback: {evaluation['feedback']}"
    
    def validate_json_structure(self, data, required_fields, method_name):
        """Validate JSON structure for ReAct methods"""
        assert isinstance(data, dict), f"{method_name} should return dict"
        for field in required_fields:
            assert field in data, f"{method_name} missing required field: {field}"
    
    def validate_reason_output(self, reasoning):
        """Validate reason() method output"""
        self.validate_json_structure(reasoning, ["reasoning", "tool_call"], "reason()")
        
        # Validate tool_call structure
        tool_call = reasoning.get("tool_call", {})
        assert isinstance(tool_call, dict), "tool_call should be dict"
        assert "tool" in tool_call, "tool_call should have 'tool' field"
        assert "input" in tool_call, "tool_call should have 'input' field"
        
        # Validate reasoning is meaningful
        reasoning_text = reasoning.get("reasoning", "")
        assert len(reasoning_text) > 10, "reasoning should be meaningful text"
    
    def validate_act_output(self, action_result):
        """Validate act() method output"""
        self.validate_json_structure(action_result, ["status", "action"], "act()")
        
        # Validate status values
        status = action_result.get("status")
        assert status in ["success", "error"], f"act() status should be 'success' or 'error', got '{status}'"
        
        # If success, should have result
        if status == "success":
            assert "result" in action_result, "Successful act() should have 'result' field"
    
    def validate_observe_output(self, observation):
        """Validate observe() method output"""
        self.validate_json_structure(observation, ["observation", "ci_status", "next_action_needed"], "observe()")
        
        # Validate ci_status values
        ci_status = observation.get("ci_status")
        assert ci_status in ["pass", "fail", "unknown"], f"ci_status should be 'pass', 'fail', or 'unknown', got '{ci_status}'"
        
        # Validate next_action_needed is boolean
        next_action = observation.get("next_action_needed")
        assert isinstance(next_action, bool), "next_action_needed should be boolean"
        
        # Validate observation text
        obs_text = observation.get("observation", "")
        assert len(obs_text) > 5, "observation should be meaningful text"
    
    
    # Individual Scenario Tests
    def test_scenario_01_syntax_error(self):
        """Test Case 1: Fix syntax error (missing colon) - Complete validation"""
        scenario_name = "seed_01_syntax"
        max_steps = self.scenario_thresholds[scenario_name]
        
        # Use orchestrator to create workspace
        from src.orchestrator import create_error_workspace
        workspace_result = create_error_workspace(scenario_name)
        
        assert workspace_result["status"] == "pass", f"Failed to create workspace: {workspace_result.get('error', 'Unknown error')}"
        
        workspace_path = workspace_result["data"]["workspace_path"]
        error_info = workspace_result["data"]["error_info"]
        scenario_description = error_info.get('description', 'Unknown error')
        
        print(f"\n=== Testing {scenario_name}: {scenario_description} ===")
        
        # Get initial CI status
        ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        initial_observation = f"Initial CI status: {ci_result}"
        
        # Create context for LLM judge
        judge_context = {
            'scenario_name': scenario_name,
            'scenario_description': scenario_description,
            'observation': initial_observation
        }
        
        # Test reason() method - JSON validation + LLM judge
        reasoning = self.agent.reason(initial_observation)
        self.validate_reason_output(reasoning)
        print(f"✓ reason() returns valid JSON structure")
        
        reasoning_eval = self.judge_react_step('reason', reasoning, judge_context)
        print(f"✓ reason() quality: {reasoning_eval['score']}/100 - {reasoning_eval['feedback'][:50]}...")
        
        # Test act() method - JSON validation + LLM judge
        action_result = self.agent.act(reasoning)
        self.validate_act_output(action_result)
        print(f"✓ act() returns valid JSON structure")
        
        action_context = judge_context.copy()
        action_context['reasoning'] = reasoning.get('reasoning', '')
        action_eval = self.judge_react_step('act', action_result, action_context)
        print(f"✓ act() quality: {action_eval['score']}/100 - {action_eval['feedback'][:50]}...")
        
        # Test observe() method - JSON validation + LLM judge
        observation = self.agent.observe(action_result)
        self.validate_observe_output(observation)
        print(f"✓ observe() returns valid JSON structure")
        
        obs_context = judge_context.copy()
        obs_context['action_result'] = action_result
        obs_eval = self.judge_react_step('observe', observation, obs_context)
        print(f"✓ observe() quality: {obs_eval['score']}/100 - {obs_eval['feedback'][:50]}...")
        
        # Test full scenario execution with LLM judge
        judge_result = self.judge_scenario_execution(scenario_name, workspace_path, max_turns=max_steps)
        scenario_data = judge_result['scenario_data']
        full_evaluation = judge_result['judge_evaluation']
        
        # Validate success
        assert scenario_data['final_result'] == "success", f"Agent should fix {scenario_description} but got '{scenario_data['final_result']}'"
        print(f"✓ Agent successfully fixed the issue")
        
        # Validate LLM judge evaluation
        self.assert_judge_quality(full_evaluation, min_score=50)
        print(f"✓ Full scenario quality: {full_evaluation['score']}/100 - {full_evaluation['feedback'][:50]}...")
        
        # Efficiency check
        assert scenario_data['total_turns'] <= max_steps, f"Agent took {scenario_data['total_turns']} turns, expected <= {max_steps}"
        print(f"✓ Agent solved in {scenario_data['total_turns']}/{max_steps} steps")
        
        print(f"✓ SCENARIO COMPLETE: {scenario_name} - All validations passed")
        
        # Clean up this test's workspace
        try:
            if Path(workspace_path).exists():
                shutil.rmtree(workspace_path)
        except (FileNotFoundError, OSError):
            pass
    
    def test_scenario_02_import_error(self):
        """Test Case 2: Fix missing import - Complete validation"""
        scenario_name = "seed_02_import"
        max_steps = self.scenario_thresholds[scenario_name]
        
        # Use orchestrator to create workspace
        from src.orchestrator import create_error_workspace
        workspace_result = create_error_workspace(scenario_name)
        
        assert workspace_result["status"] == "pass", f"Failed to create workspace: {workspace_result.get('error', 'Unknown error')}"
        
        workspace_path = workspace_result["data"]["workspace_path"]
        error_info = workspace_result["data"]["error_info"]
        scenario_description = error_info.get('description', 'Unknown error')
        
        print(f"\n=== Testing {scenario_name}: {scenario_description} ===")
        
        # Get initial CI status
        ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        initial_observation = f"Initial CI status: {ci_result}"
        
        # Create context for LLM judge
        judge_context = {
            'scenario_name': scenario_name,
            'scenario_description': scenario_description,
            'observation': initial_observation
        }
        
        # Test reason() method - JSON validation + LLM judge
        reasoning = self.agent.reason(initial_observation)
        self.validate_reason_output(reasoning)
        print(f"✓ reason() returns valid JSON structure")
        
        reasoning_eval = self.judge_react_step('reason', reasoning, judge_context)
        print(f"✓ reason() quality: {reasoning_eval['score']}/100 - {reasoning_eval['feedback'][:50]}...")
        
        # Test act() method - JSON validation + LLM judge
        action_result = self.agent.act(reasoning)
        self.validate_act_output(action_result)
        print(f"✓ act() returns valid JSON structure")
        
        action_context = judge_context.copy()
        action_context['reasoning'] = reasoning.get('reasoning', '')
        action_eval = self.judge_react_step('act', action_result, action_context)
        print(f"✓ act() quality: {action_eval['score']}/100 - {action_eval['feedback'][:50]}...")
        
        # Test observe() method - JSON validation + LLM judge
        observation = self.agent.observe(action_result)
        self.validate_observe_output(observation)
        print(f"✓ observe() returns valid JSON structure")
        
        obs_context = judge_context.copy()
        obs_context['action_result'] = action_result
        obs_eval = self.judge_react_step('observe', observation, obs_context)
        print(f"✓ observe() quality: {obs_eval['score']}/100 - {obs_eval['feedback'][:50]}...")
        
        # Test full scenario execution with LLM judge
        judge_result = self.judge_scenario_execution(scenario_name, workspace_path, max_turns=max_steps)
        scenario_data = judge_result['scenario_data']
        full_evaluation = judge_result['judge_evaluation']
        
        # Validate success
        assert scenario_data['final_result'] == "success", f"Agent should fix {scenario_description} but got '{scenario_data['final_result']}'"
        print(f"✓ Agent successfully fixed the issue")
        
        # Validate LLM judge evaluation
        self.assert_judge_quality(full_evaluation, min_score=50)
        print(f"✓ Full scenario quality: {full_evaluation['score']}/100 - {full_evaluation['feedback'][:50]}...")
        
        # Efficiency check
        assert scenario_data['total_turns'] <= max_steps, f"Agent took {scenario_data['total_turns']} turns, expected <= {max_steps}"
        print(f"✓ Agent solved in {scenario_data['total_turns']}/{max_steps} steps")
        
        print(f"✓ SCENARIO COMPLETE: {scenario_name} - All validations passed")
        
        # Clean up this test's workspace
        try:
            if Path(workspace_path).exists():
                shutil.rmtree(workspace_path)
        except (FileNotFoundError, OSError):
            pass
    
    def test_scenario_03_test_failure(self):
        """Test Case 3: Fix wrong test assertion - Complete validation"""
        scenario_name = "seed_03_test"
        max_steps = self.scenario_thresholds[scenario_name]
        
        # Use orchestrator to create workspace
        from src.orchestrator import create_error_workspace
        workspace_result = create_error_workspace(scenario_name)
        
        assert workspace_result["status"] == "pass", f"Failed to create workspace: {workspace_result.get('error', 'Unknown error')}"
        
        workspace_path = workspace_result["data"]["workspace_path"]
        error_info = workspace_result["data"]["error_info"]
        scenario_description = error_info.get('description', 'Unknown error')
        
        print(f"\n=== Testing {scenario_name}: {scenario_description} ===")
        
        # Get initial CI status
        ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        initial_observation = f"Initial CI status: {ci_result}"
        
        # Create context for LLM judge
        judge_context = {
            'scenario_name': scenario_name,
            'scenario_description': scenario_description,
            'observation': initial_observation
        }
        
        # Test reason() method - JSON validation + LLM judge
        reasoning = self.agent.reason(initial_observation)
        self.validate_reason_output(reasoning)
        print(f"✓ reason() returns valid JSON structure")
        
        reasoning_eval = self.judge_react_step('reason', reasoning, judge_context)
        print(f"✓ reason() quality: {reasoning_eval['score']}/100 - {reasoning_eval['feedback'][:50]}...")
        
        # Test act() method - JSON validation + LLM judge
        action_result = self.agent.act(reasoning)
        self.validate_act_output(action_result)
        print(f"✓ act() returns valid JSON structure")
        
        action_context = judge_context.copy()
        action_context['reasoning'] = reasoning.get('reasoning', '')
        action_eval = self.judge_react_step('act', action_result, action_context)
        print(f"✓ act() quality: {action_eval['score']}/100 - {action_eval['feedback'][:50]}...")
        
        # Test observe() method - JSON validation + LLM judge
        observation = self.agent.observe(action_result)
        self.validate_observe_output(observation)
        print(f"✓ observe() returns valid JSON structure")
        
        obs_context = judge_context.copy()
        obs_context['action_result'] = action_result
        obs_eval = self.judge_react_step('observe', observation, obs_context)
        print(f"✓ observe() quality: {obs_eval['score']}/100 - {obs_eval['feedback'][:50]}...")
        
        # Test full scenario execution with LLM judge
        judge_result = self.judge_scenario_execution(scenario_name, workspace_path, max_turns=max_steps)
        scenario_data = judge_result['scenario_data']
        full_evaluation = judge_result['judge_evaluation']
        
        # Validate success
        assert scenario_data['final_result'] == "success", f"Agent should fix {scenario_description} but got '{scenario_data['final_result']}'"
        print(f"✓ Agent successfully fixed the issue")
        
        # Validate LLM judge evaluation
        self.assert_judge_quality(full_evaluation, min_score=50)
        print(f"✓ Full scenario quality: {full_evaluation['score']}/100 - {full_evaluation['feedback'][:50]}...")
        
        # Efficiency check
        assert scenario_data['total_turns'] <= max_steps, f"Agent took {scenario_data['total_turns']} turns, expected <= {max_steps}"
        print(f"✓ Agent solved in {scenario_data['total_turns']}/{max_steps} steps")
        
        print(f"✓ SCENARIO COMPLETE: {scenario_name} - All validations passed")
        
        # Clean up this test's workspace
        try:
            if Path(workspace_path).exists():
                shutil.rmtree(workspace_path)
        except (FileNotFoundError, OSError):
            pass
    
    def test_scenario_04_dependency_error(self):
        """Test Case 4: Fix missing dependency - Complete validation"""
        scenario_name = "seed_04_dependency"
        max_steps = self.scenario_thresholds[scenario_name]
        
        # Use orchestrator to create workspace
        from src.orchestrator import create_error_workspace
        workspace_result = create_error_workspace(scenario_name)
        
        assert workspace_result["status"] == "pass", f"Failed to create workspace: {workspace_result.get('error', 'Unknown error')}"
        
        workspace_path = workspace_result["data"]["workspace_path"]
        error_info = workspace_result["data"]["error_info"]
        scenario_description = error_info.get('description', 'Unknown error')
        
        print(f"\n=== Testing {scenario_name}: {scenario_description} ===")
        
        # Get initial CI status
        ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        initial_observation = f"Initial CI status: {ci_result}"
        
        # Create context for LLM judge
        judge_context = {
            'scenario_name': scenario_name,
            'scenario_description': scenario_description,
            'observation': initial_observation
        }
        
        # Test reason() method - JSON validation + LLM judge
        reasoning = self.agent.reason(initial_observation)
        self.validate_reason_output(reasoning)
        print(f"✓ reason() returns valid JSON structure")
        
        reasoning_eval = self.judge_react_step('reason', reasoning, judge_context)
        print(f"✓ reason() quality: {reasoning_eval['score']}/100 - {reasoning_eval['feedback'][:50]}...")
        
        # Test act() method - JSON validation + LLM judge
        action_result = self.agent.act(reasoning)
        self.validate_act_output(action_result)
        print(f"✓ act() returns valid JSON structure")
        
        action_context = judge_context.copy()
        action_context['reasoning'] = reasoning.get('reasoning', '')
        action_eval = self.judge_react_step('act', action_result, action_context)
        print(f"✓ act() quality: {action_eval['score']}/100 - {action_eval['feedback'][:50]}...")
        
        # Test observe() method - JSON validation + LLM judge
        observation = self.agent.observe(action_result)
        self.validate_observe_output(observation)
        print(f"✓ observe() returns valid JSON structure")
        
        obs_context = judge_context.copy()
        obs_context['action_result'] = action_result
        obs_eval = self.judge_react_step('observe', observation, obs_context)
        print(f"✓ observe() quality: {obs_eval['score']}/100 - {obs_eval['feedback'][:50]}...")
        
        # Test full scenario execution with LLM judge
        judge_result = self.judge_scenario_execution(scenario_name, workspace_path, max_turns=max_steps)
        scenario_data = judge_result['scenario_data']
        full_evaluation = judge_result['judge_evaluation']
        
        # Validate success
        assert scenario_data['final_result'] == "success", f"Agent should fix {scenario_description} but got '{scenario_data['final_result']}'"
        print(f"✓ Agent successfully fixed the issue")
        
        # Validate LLM judge evaluation
        self.assert_judge_quality(full_evaluation, min_score=50)
        print(f"✓ Full scenario quality: {full_evaluation['score']}/100 - {full_evaluation['feedback'][:50]}...")
        
        # Efficiency check
        assert scenario_data['total_turns'] <= max_steps, f"Agent took {scenario_data['total_turns']} turns, expected <= {max_steps}"
        print(f"✓ Agent solved in {scenario_data['total_turns']}/{max_steps} steps")
        
        print(f"✓ SCENARIO COMPLETE: {scenario_name} - All validations passed")
        
        # Clean up this test's workspace
        try:
            if Path(workspace_path).exists():
                shutil.rmtree(workspace_path)
        except (FileNotFoundError, OSError):
            pass
    
    def test_scenario_05_yaml_config_error(self):
        """Test Case 5: Fix YAML config syntax error - Complete validation"""
        scenario_name = "seed_05_yaml"
        max_steps = self.scenario_thresholds[scenario_name]
        
        # Use orchestrator to create workspace
        from src.orchestrator import create_error_workspace
        workspace_result = create_error_workspace(scenario_name)
        
        assert workspace_result["status"] == "pass", f"Failed to create workspace: {workspace_result.get('error', 'Unknown error')}"
        
        workspace_path = workspace_result["data"]["workspace_path"]
        error_info = workspace_result["data"]["error_info"]
        scenario_description = error_info.get('description', 'Unknown error')
        
        print(f"\n=== Testing {scenario_name}: {scenario_description} ===")
        
        # Get initial CI status
        ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        initial_observation = f"Initial CI status: {ci_result}"
        
        # Create context for LLM judge
        judge_context = {
            'scenario_name': scenario_name,
            'scenario_description': scenario_description,
            'observation': initial_observation
        }
        
        # Test reason() method - JSON validation + LLM judge
        reasoning = self.agent.reason(initial_observation)
        self.validate_reason_output(reasoning)
        print(f"✓ reason() returns valid JSON structure")
        
        reasoning_eval = self.judge_react_step('reason', reasoning, judge_context)
        print(f"✓ reason() quality: {reasoning_eval['score']}/100 - {reasoning_eval['feedback'][:50]}...")
        
        # Test act() method - JSON validation + LLM judge
        action_result = self.agent.act(reasoning)
        self.validate_act_output(action_result)
        print(f"✓ act() returns valid JSON structure")
        
        action_context = judge_context.copy()
        action_context['reasoning'] = reasoning.get('reasoning', '')
        action_eval = self.judge_react_step('act', action_result, action_context)
        print(f"✓ act() quality: {action_eval['score']}/100 - {action_eval['feedback'][:50]}...")
        
        # Test observe() method - JSON validation + LLM judge
        observation = self.agent.observe(action_result)
        self.validate_observe_output(observation)
        print(f"✓ observe() returns valid JSON structure")
        
        obs_context = judge_context.copy()
        obs_context['action_result'] = action_result
        obs_eval = self.judge_react_step('observe', observation, obs_context)
        print(f"✓ observe() quality: {obs_eval['score']}/100 - {obs_eval['feedback'][:50]}...")
        
        # Test full scenario execution with LLM judge
        judge_result = self.judge_scenario_execution(scenario_name, workspace_path, max_turns=max_steps)
        scenario_data = judge_result['scenario_data']
        full_evaluation = judge_result['judge_evaluation']
        
        # Validate success
        assert scenario_data['final_result'] == "success", f"Agent should fix {scenario_description} but got '{scenario_data['final_result']}'"
        print(f"✓ Agent successfully fixed the issue")
        
        # Validate LLM judge evaluation
        self.assert_judge_quality(full_evaluation, min_score=50)
        print(f"✓ Full scenario quality: {full_evaluation['score']}/100 - {full_evaluation['feedback'][:50]}...")
        
        # Efficiency check
        assert scenario_data['total_turns'] <= max_steps, f"Agent took {scenario_data['total_turns']} turns, expected <= {max_steps}"
        print(f"✓ Agent solved in {scenario_data['total_turns']}/{max_steps} steps")
        
        print(f"✓ SCENARIO COMPLETE: {scenario_name} - All validations passed")
        
        # Clean up this test's workspace
        try:
            if Path(workspace_path).exists():
                shutil.rmtree(workspace_path)
        except (FileNotFoundError, OSError):
            pass
    
    def test_scenario_06_multi_step_chain(self):
        """Test Case 6: Fix multiple related issues - Complete validation"""
        scenario_name = "seed_06_multi"
        max_steps = self.scenario_thresholds[scenario_name]
        
        # Use orchestrator to create workspace
        from src.orchestrator import create_error_workspace
        workspace_result = create_error_workspace(scenario_name)
        
        assert workspace_result["status"] == "pass", f"Failed to create workspace: {workspace_result.get('error', 'Unknown error')}"
        
        workspace_path = workspace_result["data"]["workspace_path"]
        error_info = workspace_result["data"]["error_info"]
        scenario_description = error_info.get('description', 'Unknown error')
        
        print(f"\n=== Testing {scenario_name}: {scenario_description} ===")
        
        # Get initial CI status
        ci_result = execute_tool_in_workspace(workspace_path, "run_ci_pipeline", "")
        initial_observation = f"Initial CI status: {ci_result}"
        
        # Create context for LLM judge
        judge_context = {
            'scenario_name': scenario_name,
            'scenario_description': scenario_description,
            'observation': initial_observation
        }
        
        # Test reason() method - JSON validation + LLM judge
        reasoning = self.agent.reason(initial_observation)
        self.validate_reason_output(reasoning)
        print(f"✓ reason() returns valid JSON structure")
        
        reasoning_eval = self.judge_react_step('reason', reasoning, judge_context)
        print(f"✓ reason() quality: {reasoning_eval['score']}/100 - {reasoning_eval['feedback'][:50]}...")
        
        # Test act() method - JSON validation + LLM judge
        action_result = self.agent.act(reasoning)
        self.validate_act_output(action_result)
        print(f"✓ act() returns valid JSON structure")
        
        action_context = judge_context.copy()
        action_context['reasoning'] = reasoning.get('reasoning', '')
        action_eval = self.judge_react_step('act', action_result, action_context)
        print(f"✓ act() quality: {action_eval['score']}/100 - {action_eval['feedback'][:50]}...")
        
        # Test observe() method - JSON validation + LLM judge
        observation = self.agent.observe(action_result)
        self.validate_observe_output(observation)
        print(f"✓ observe() returns valid JSON structure")
        
        obs_context = judge_context.copy()
        obs_context['action_result'] = action_result
        obs_eval = self.judge_react_step('observe', observation, obs_context)
        print(f"✓ observe() quality: {obs_eval['score']}/100 - {obs_eval['feedback'][:50]}...")
        
        # Test full scenario execution with LLM judge
        judge_result = self.judge_scenario_execution(scenario_name, workspace_path, max_turns=max_steps)
        scenario_data = judge_result['scenario_data']
        full_evaluation = judge_result['judge_evaluation']
        
        # Validate success
        assert scenario_data['final_result'] == "success", f"Agent should fix {scenario_description} but got '{scenario_data['final_result']}'"
        print(f"✓ Agent successfully fixed the issue")
        
        # Validate LLM judge evaluation
        self.assert_judge_quality(full_evaluation, min_score=50)
        print(f"✓ Full scenario quality: {full_evaluation['score']}/100 - {full_evaluation['feedback'][:50]}...")
        
        # Efficiency check
        assert scenario_data['total_turns'] <= max_steps, f"Agent took {scenario_data['total_turns']} turns, expected <= {max_steps}"
        print(f"✓ Agent solved in {scenario_data['total_turns']}/{max_steps} steps")
        
        print(f"✓ SCENARIO COMPLETE: {scenario_name} - All validations passed")
        
        # Clean up this test's workspace
        try:
            if Path(workspace_path).exists():
                shutil.rmtree(workspace_path)
        except (FileNotFoundError, OSError):
            pass
    
    
    # Core Functionality Tests - These tests should FAIL when methods are NOT implemented
    def test_reason_method_implemented(self):
        """Test that reason method is implemented (user must implement this)"""
        try:
            result = self.agent.reason("Test observation: CI failed with syntax error")
        except NotImplementedError:
            pytest.fail("User must implement reason() method in src/ci_agent.py")
    
    def test_act_method_implemented(self):
        """Test that act method is implemented (user must implement this)"""
        test_reasoning = {"reasoning": "test", "tool_call": {"tool": "test_tool", "input": "test_input"}}
        try:
            result = self.agent.act(test_reasoning)
        except NotImplementedError:
            pytest.fail("User must implement act() method in src/ci_agent.py")
    
    def test_observe_method_implemented(self):
        """Test that observe method is implemented (user must implement this)"""
        test_action_result = {"status": "success", "action": "test_action", "result": {}}
        try:
            result = self.agent.observe(test_action_result)
        except NotImplementedError:
            pytest.fail("User must implement observe() method in src/ci_agent.py")
