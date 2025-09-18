import subprocess

def analyze_file(filename):
    """Read file and identify errors"""
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        content = ""
        for i, line in enumerate(lines, 1):
            content += f"Line {i}: {line.rstrip()}\n"
            
        return {"action": "analyze_file", "status": "pass", "data": {"content": content}}
    except Exception as e:
        return {"action": "analyze_file", "status": "fail", "error": f"Error reading {filename}: {e}"}

def analyze_test_failure(test_path):
    """Analyze specific test failure"""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v"],
            capture_output=True, text=True
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return {"action": "analyze_test_failure", "status": "pass", "data": {"output": output}}
        else:
            return {"action": "analyze_test_failure", "status": "fail", "error": output}
    except Exception as e:
        return {"action": "analyze_test_failure", "status": "fail", "error": f"Error analyzing test: {e}"}
