from __future__ import annotations

import os
import json
import hashlib
from typing import Any, Optional, Dict, List

from dotenv import load_dotenv
from openai import OpenAI


# Use content-based cache files that persist across test runs
def _get_cache_file(input_hash: str) -> str:
    """Get cache file path based on input content hash for persistence across runs."""
    cache_dir = os.path.join(os.getcwd(), ".pytest_cache")
    # Use first 8 chars of hash to avoid super long filenames but still avoid collisions
    return os.path.join(cache_dir, f"cache_{input_hash[:8]}.json")


def _get_input_hash(prompt: str, system_msg: str, model: str, max_tokens: int) -> str:
    """Create a hash of input parameters for caching."""
    input_str = f"{system_msg}|{prompt}|{model}|{max_tokens}"
    return hashlib.sha256(input_str.encode()).hexdigest()[:16]


def try_load_env() -> None:
    here = os.path.dirname(__file__)
    try:
        load_dotenv(os.path.join(here, "..", ".env.local"))
    except Exception:
        pass


try_load_env()


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client with proper configuration."""
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = "https://api.openai.com/v1"
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required for LLM usage")
    return OpenAI(api_key=api_key, base_url=api_base)


def call_openai_chat(
    prompt: str,
    system_msg: str = None,
    *,  # Force remaining arguments to be keyword-only
    model: str = "gpt-4o-mini",
    max_tokens: int = 1000,
    stop: List[str] = None,
    seed: int = None,
    response_format: Dict[str, str] = None,
    use_cache: bool = True,
) -> str:
    # Check cache first if caching is enabled
    if use_cache:
        cache_key = _get_input_hash(prompt, system_msg or "", model, max_tokens)
        cache_file = _get_cache_file(cache_key)
        
        # Check content-based cache file
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    if cache_key in cache_data:
                        return cache_data[cache_key]
        except (json.JSONDecodeError, IOError, OSError):
            pass  # Continue to API call if cache read fails
    
    client = get_openai_client()
    
    # Construct messages array with optional system message
    messages = []
    if system_msg:
        messages.append({"role": "system", "content": system_msg})
    messages.append({"role": "user", "content": prompt})

    try:
        # Build kwargs dict with only provided non-None values for cleaner API calls
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.0,  # Force deterministic temperature
            "top_p": 0.1,        # Very low top_p for more deterministic results
            "n": 1,              # Always single response for consistency
            "max_tokens": max_tokens,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        }
        
        # Add optional parameters only if they're provided to avoid API conflicts
        if stop is not None:
            kwargs["stop"] = stop
        
        # Try to add seed if provided, but handle gracefully if API doesn't support it
        if seed is not None:
            kwargs["seed"] = seed
            
        if response_format is not None:
            kwargs["response_format"] = response_format
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        
        # Cache the response if caching is enabled
        if use_cache:
            cache_file = _get_cache_file(cache_key)
            
            # Save to content-based cache file (persists across runs!)
            try:
                # Read existing cache from content-based file
                cache_data = {}
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                
                # Add new entry
                cache_data[cache_key] = content
                
                # Write back to content-based file
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)
                
            except Exception:
                pass  # Continue silently if caching fails
            
        return content
    except Exception as e:
        return f"Error calling API: {str(e)}"


class CachedLLM:
    """LangChain-compatible LLM wrapper that uses persistent file-based caching."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
    
    def invoke(self, prompt: str, system_msg: str = None) -> Any:
        """Invoke the LLM with caching, compatible with LangChain interface."""
        content = call_openai_chat(prompt, system_msg, model=self.model)
        
        # Return an object with .content attribute to match LangChain's interface
        class Response:
            def __init__(self, content: str):
                self.content = content
            
            def __str__(self):
                return self.content
        
        return Response(content)


def get_llm() -> Any:
    """Get cached LLM instance compatible with existing code."""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return CachedLLM(model=model)


__all__ = ["get_llm"]