"""LLM Judge for ReAct Agent Evaluation"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from src.llm import get_llm


def format_rubric_header() -> str:
    """Format the standard rubric header for JSON-only judge responses."""
    return (
        "You are a strict JSON-only judge.\n"
        "Output only a single JSON object with keys: pass (boolean), score (0-100), feedback (string), reasons (array of strings).\n"
        "Do not include any extra text.\n"
    )


def build_prompt(
    task_name: str, rubric: str, input_data: Dict[str, Any], output_data: Dict[str, Any]
) -> str:
    """Build a standardized prompt for LLM judge evaluation."""
    header = format_rubric_header()
    return (
        f"{header}\n"
        f"Task: {task_name}\n"
        f"Rubric:\n{rubric}\n\n"
        f"Input:\n{json.dumps(input_data, ensure_ascii=False)}\n\n"
        f"Output:\n{json.dumps(output_data, ensure_ascii=False)}\n\n"
        "Respond with JSON now."
    )


def invoke_judge(llm: Any, prompt: str) -> Dict[str, Any]:
    """Invoke the LLM judge with standardized response handling."""
    completion = llm.invoke(prompt)
    content = getattr(completion, "content", str(completion))

    try:
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        # Fallback for malformed JSON
        data = {
            "pass": False,
            "score": 0,
            "feedback": f"Failed to parse judge response: {content[:200]}...",
            "reasons": ["JSON parsing error"],
        }

    # Shape normalization
    out: Dict[str, Any] = {
        "pass": bool(data.get("pass", False)),
        "score": int(data.get("score", 0)),
        "feedback": str(data.get("feedback", "")),
        "reasons": list(data.get("reasons", [])),
    }

    return out


def judge_reasoning_output(
    reasoning_output: Dict[str, Any], context: Dict[str, Any], llm: Any
) -> Dict[str, Any]:
    """Judge the quality of a reasoning step output."""
    rubric = (
        "- Reasoning text accurately identifies the problem from the observation.\n"
        "- Problem analysis is technically correct and specific (not vague).\n"
        "- Tool selection is appropriate for the identified problem.\n"
        "- Tool parameters are correct and well-formed for the chosen tool.\n"
        "- Reasoning demonstrates understanding of CI/CD troubleshooting.\n"
        "- Tool call structure follows expected format: {tool: string, input: string}.\n"
        "- Input parameters are relevant to fixing the observed CI issue.\n"
        "- No hallucination of tools or parameters that don't exist.\n"
        "- Reasoning is clear and follows logical problem-solving steps.\n"
        "- Addresses the specific scenario type (syntax, import, test, dependency, yaml, multi).\n"
    )

    input_data = {
        "scenario": context.get("scenario_name", "Unknown"),
        "observation": context.get("observation", "No observation"),
        "scenario_description": context.get("scenario_description", "Unknown"),
    }

    prompt = build_prompt(
        "Reasoning Step Evaluation", rubric, input_data, reasoning_output
    )
    return invoke_judge(llm, prompt)


def judge_action_output(
    action_output: Dict[str, Any], context: Dict[str, Any], llm: Any
) -> Dict[str, Any]:
    """Judge the quality of an action step output."""
    rubric = (
        "- Action executed successfully without errors (status: pass).\n"
        "- Action aligns with the previous reasoning step.\n"
        "- Tool parameters were technically correct and properly formatted.\n"
        "- Action contributes meaningfully to solving the CI problem.\n"
        "- Error handling is appropriate if action failed.\n"
        "- Result contains relevant information about the action outcome.\n"
        "- Action follows expected format: {status: string, action: string, input: string, result: dict}.\n"
        "- No unnecessary or harmful actions performed.\n"
        "- Action is efficient and targeted (not overly broad).\n"
        "- Proper use of available CI tools (run_ci_pipeline, fix_syntax_error, etc.).\n"
    )

    input_data = {
        "scenario": context.get("scenario_name", "Unknown"),
        "previous_reasoning": context.get("reasoning", "No reasoning"),
        "scenario_description": context.get("scenario_description", "Unknown"),
    }

    prompt = build_prompt("Action Step Evaluation", rubric, input_data, action_output)
    return invoke_judge(llm, prompt)


def judge_observation_output(
    observation_output: Dict[str, Any], context: Dict[str, Any], llm: Any
) -> Dict[str, Any]:
    """Judge the quality of an observation step output."""
    rubric = (
        "- Observation accurately interprets the action results.\n"
        "- All important information from action result is captured.\n"
        "- CI status assessment is correct (pass/fail based on action result).\n"
        "- 'Next action needed' decision is logical and appropriate.\n"
        "- Observation text is clear, informative, and specific.\n"
        "- Correctly identifies if the problem is solved or needs more work.\n"
        "- Observation follows expected format: {observation: string, ci_status: string, next_action_needed: boolean}.\n"
        "- No misinterpretation of action results or CI status.\n"
        "- Provides actionable insights for next steps if needed.\n"
        "- Demonstrates understanding of CI pipeline success/failure indicators.\n"
    )

    input_data = {
        "scenario": context.get("scenario_name", "Unknown"),
        "action_result": context.get("action_result", {}),
        "scenario_description": context.get("scenario_description", "Unknown"),
    }

    prompt = build_prompt(
        "Observation Step Evaluation", rubric, input_data, observation_output
    )
    return invoke_judge(llm, prompt)


def judge_full_scenario(scenario_data: Dict[str, Any], llm: Any) -> Dict[str, Any]:
    """Judge the overall performance across all steps in a scenario."""
    rubric = (
        "- Agent successfully fixed the CI issue (final result: success).\n"
        "- Solution was achieved efficiently (reasonable number of steps).\n"
        "- Each ReAct step (reason, act, observe) was high quality.\n"
        "- Agent demonstrated proper CI/CD troubleshooting methodology.\n"
        "- No unnecessary or harmful actions were taken.\n"
        "- Agent correctly identified and addressed the specific problem type.\n"
        "- Final CI status shows all checks passing.\n"
        "- Agent stopped appropriately when problem was solved.\n"
        "- Overall approach was systematic and logical.\n"
        "- Agent handled any errors or setbacks appropriately.\n"
    )

    input_data = {
        "scenario_name": scenario_data.get("scenario_name", "Unknown"),
        "scenario_description": scenario_data.get("scenario_description", "Unknown"),
        "total_steps": len(scenario_data.get("steps", [])),
        "final_result": scenario_data.get("final_result", "unknown"),
    }

    output_data = {
        "steps": scenario_data.get("steps", []),
        "final_result": scenario_data.get("final_result", "unknown"),
        "total_turns": scenario_data.get("total_turns", 0),
    }

    prompt = build_prompt("Full Scenario Evaluation", rubric, input_data, output_data)
    return invoke_judge(llm, prompt)


__all__ = [
    "judge_reasoning_output",
    "judge_action_output",
    "judge_observation_output",
    "judge_full_scenario",
]
