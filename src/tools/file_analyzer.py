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

