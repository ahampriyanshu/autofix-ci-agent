#!/usr/bin/env python3

import sys
import shutil
import importlib
from pathlib import Path
from create_baseline import create_baseline


def induce_error(seed_name, workspace_name=None):
    workspaces_dir = Path("workspaces")
    workspaces_dir.mkdir(exist_ok=True)
    
    if workspace_name is None:
        workspace_name = seed_name
    
    workspace_path = workspaces_dir / workspace_name
    
    if workspace_path.exists():
        shutil.rmtree(workspace_path)
    
    baseline_path = create_baseline("temp_baseline")
    shutil.copytree(baseline_path, workspace_path)
    shutil.rmtree(baseline_path)
    
    try:
        seed_module = importlib.import_module(f"scenarios.{seed_name}")
        error_info = seed_module.induce_errors(workspace_path)
        
        return {
            "workspace": str(workspace_path),
            "seed": seed_name,
            "error_info": error_info,
            "status": "success"
        }
        
    except ImportError:
        return {"status": "error", "message": f"Seed script not found: scenarios/{seed_name}.py"}
    
    except Exception as e:
        return {"status": "error", "message": f"Error applying seed {seed_name}: {str(e)}"}


def list_available_seeds():
    scenarios_dir = Path("scenarios")
    if not scenarios_dir.exists():
        return []
    
    seed_files = list(scenarios_dir.glob("seed_*.py"))
    seeds = [f.stem for f in seed_files]
    
    for seed in sorted(seeds):
        print(seed)
    
    return seeds


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 induce_error.py <seed_name> [workspace_name]")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_available_seeds()
        sys.exit(0)
    
    seed_name = sys.argv[1]
    workspace_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not seed_name.startswith("seed_"):
        sys.exit(1)
    
    result = induce_error(seed_name, workspace_name)
    
    if result["status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
