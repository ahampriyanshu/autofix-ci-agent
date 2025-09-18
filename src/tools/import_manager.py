def add_import(params):
    """Add import: file:import_statement"""
    try:
        file_path, import_stmt = params.split(":", 1)
        
        with open(file_path, 'r') as f:
            content = f.read()
            
        if import_stmt not in content:
            content = import_stmt + "\n" + content
            
        with open(file_path, 'w') as f:
            f.write(content)
            
        return {"action": "add_import", "status": "pass"}
    except Exception as e:
        return {"action": "add_import", "status": "fail", "error": f"Error adding import: {e}"}

def remove_unused_import(params):
    """Remove unused import: file:import_statement"""
    try:
        file_path, import_stmt = params.split(":", 1)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            if import_stmt.strip() not in line:
                new_lines.append(line)
                
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
            
        return {"action": "remove_unused_import", "status": "pass"}
    except Exception as e:
        return {"action": "remove_unused_import", "status": "fail", "error": f"Error removing import: {e}"}
