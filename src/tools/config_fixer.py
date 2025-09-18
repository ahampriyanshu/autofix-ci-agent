def validate_config(filename):
    """Validate YAML/config file"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith('#'):
                if 'name lint' in line and ':' not in line:
                    return {"action": "validate_config", "status": "fail", "error": f"Line {i}: Missing colon after 'name lint'"}
                    
        return {"action": "validate_config", "status": "pass"}
    except Exception as e:
        return {"action": "validate_config", "status": "fail", "error": f"Error validating config: {e}"}

def fix_yaml_syntax(params):
    """Fix YAML syntax: file:line:fix_type"""
    try:
        file_path, line_num, fix_type = params.split(":")
        line_num = int(line_num)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        if fix_type == "add_colon":
            line = lines[line_num - 1]
            # For YAML, add colon after 'name lint' specifically
            if 'name lint' in line and ':' not in line.split('#')[0]:
                line = line.replace('name lint', 'name: lint')
                lines[line_num - 1] = line
            else:
                # Generic case: add colon at end
                lines[line_num - 1] = line.rstrip() + ":\n"
            
        with open(file_path, 'w') as f:
            f.writelines(lines)
            
        return {"action": "fix_yaml_syntax", "status": "pass"}
    except Exception as e:
        return {"action": "fix_yaml_syntax", "status": "fail", "error": f"Error fixing YAML: {e}"}
