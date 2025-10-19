def fix_test_assertion(params):
    """Fix test assertion: file:line:correct_value or file:line:param_name:correct_value"""
    try:
        parts = params.split(":")
        if len(parts) == 3:
            file_path, line_num, correct_value = parts
        elif len(parts) == 4:
            file_path, line_num, _, correct_value = parts  # Skip param name
        else:
            raise ValueError(f"Expected 3 or 4 parts, got {len(parts)}")
        line_num = int(line_num)

        with open(file_path, "r") as f:
            lines = f.readlines()

        line = lines[line_num - 1]
        if "==" in line:
            parts = line.split("==")
            # Preserve original line ending
            ending = "\n" if line.endswith("\n") else ""
            lines[line_num - 1] = parts[0] + f"== {correct_value}{ending}"

        with open(file_path, "w") as f:
            f.writelines(lines)

        return {"action": "fix_test_assertion", "status": "pass"}
    except Exception as e:
        return {
            "action": "fix_test_assertion",
            "status": "fail",
            "error": f"Error fixing test: {e}",
        }
