def add_dependency(package_name):
    """Add package to requirements.txt"""
    try:
        with open("requirements.txt", 'a') as f:
            f.write(f"\n{package_name}\n")
        return {"action": "add_dependency", "status": "pass"}
    except Exception as e:
        return {"action": "add_dependency", "status": "fail", "error": f"Error adding dependency: {e}"}
