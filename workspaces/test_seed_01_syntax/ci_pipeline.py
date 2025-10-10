#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
import yaml
import ast
import json


class CIPipeline:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)

    def run_all_checks(self):
        checks = [
            ("syntax", self.check_syntax),
            ("lint", self.check_lint),
            ("tests", self.check_tests),
            ("dependencies", self.check_dependencies),
            ("config", self.check_config),
            ("security", self.check_security)
        ]

        results = []
        all_passed = True

        for test_name, check_func in checks:
            try:
                passed, error = check_func()
                result = {"test": test_name, "status": "pass" if passed else "fail"}

                if not passed:
                    result["error"] = error
                    all_passed = False

                results.append(result)

            except Exception as e:
                results.append({"test": test_name, "status": "fail", "error": str(e)})
                all_passed = False

        return {
            "overall_status": "pass" if all_passed else "fail",
            "checks": results
        }

    def check_syntax(self):
        python_files = list(self.repo_path.rglob("*.py"))

        for py_file in python_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                return False, f"Syntax error in {py_file}: {e.msg} at line {e.lineno}"
            except Exception as e:
                return False, f"Error parsing {py_file}: {str(e)}"

        return True, None

    def check_lint(self):
        try:
            result = subprocess.run(
                ["python3", "-m", "flake8", ".", "--max-line-length=100"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, None
            else:
                return False, f"Linting issues:\n{result.stdout}"

        except subprocess.TimeoutExpired:
            return False, "Linting check timed out"
        except FileNotFoundError:
            return False, "flake8 not installed"

    def check_tests(self):
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", "-v", "-p", "no:cacheprovider"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True, None
            else:
                return False, f"Test failures:\n{result.stdout}\n{result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Tests timed out"
        except FileNotFoundError:
            return False, "pytest not installed"

    def check_dependencies(self):
        req_file = self.repo_path / "requirements.txt"

        if not req_file.exists():
            return False, "requirements.txt not found"

        try:
            with open(req_file, 'r') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if not any(c.isalnum() for c in line):
                        return False, f"Invalid dependency at line {line_num}: {line}"

            return True, None

        except Exception as e:
            return False, f"Error reading requirements.txt: {str(e)}"

    def check_config(self):
        yaml_files = list(self.repo_path.rglob("*.yml")) + list(self.repo_path.rglob("*.yaml"))

        if not yaml_files:
            return True, None

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                return False, f"YAML error in {yaml_file}: {str(e)}"
            except Exception as e:
                return False, f"Error reading {yaml_file}: {str(e)}"

        return True, None

    def check_security(self):
        python_files = list(self.repo_path.rglob("*.py"))
        security_issues = []

        for py_file in python_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    lines = f.read().split('\n')

                for line_num, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    patterns = ['api_key', 'secret_key', 'password']
                    if any(pattern in line_lower for pattern in patterns):
                        if '=' in line and any(quote in line for quote in ['"', "'"]):
                            value_part = line.split('=', 1)[1].strip()
                            if value_part.startswith(('"', "'")) and len(value_part) > 10:
                                security_issues.append(f"{py_file}:{line_num}")

            except Exception:
                continue

        if security_issues:
            return False, f"Hardcoded secrets found: {', '.join(security_issues)}"

        return True, None


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    pipeline = CIPipeline(repo_path)
    result = pipeline.run_all_checks()

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
