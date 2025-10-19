def fix_syntax_error(params):
    """Fix syntax error: file:line:fix_type"""
    try:
        file_path, line_num, fix_type = params.split(":")
        line_num = int(line_num)

        with open(file_path, "r") as f:
            lines = f.readlines()

        if fix_type == "add_colon":
            line = lines[line_num - 1].rstrip()
            # For function definitions, add colon after the closing parenthesis
            if line.startswith("def ") and ")" in line:
                # Split function definition from comment
                if "#" in line:
                    func_part = line.split("#")[0].strip()
                    comment_part = "#" + "#".join(line.split("#")[1:])
                else:
                    func_part = line.strip()
                    comment_part = ""

                # Find parenthesis in function part only
                paren_pos = func_part.rfind(")")
                if paren_pos != -1:
                    # Add colon after parenthesis in function part
                    fixed_func = func_part[: paren_pos + 1] + ":"
                    if comment_part:
                        line = fixed_func + "  " + comment_part
                    else:
                        line = fixed_func
                else:
                    # No parenthesis found, add colon at end of function part
                    line = func_part + ":"
            else:
                # Generic case: add colon at end if not already there
                if not line.endswith(":"):
                    line = line + ":"
            lines[line_num - 1] = line + "\n"
        elif fix_type == "add_parenthesis":
            lines[line_num - 1] = (
                lines[line_num - 1].replace("print ", "print(").rstrip() + ")\n"
            )
        elif fix_type == "fix_indentation":
            lines[line_num - 1] = "    " + lines[line_num - 1].lstrip()
        elif fix_type == "add_blank_lines":
            # Ensure exactly 2 blank lines before the specified line
            # First, remove any existing blank lines before this line
            while line_num > 1 and lines[line_num - 2].strip() == "":
                lines.pop(line_num - 2)
                line_num -= 1
            # Then add exactly 2 blank lines
            lines.insert(line_num - 1, "\n")
            lines.insert(line_num - 1, "\n")
        elif fix_type == "remove_blank_lines":
            # Remove excess blank lines before the specified line
            while line_num > 1 and lines[line_num - 2].strip() == "":
                lines.pop(line_num - 2)
                line_num -= 1
            # Add back exactly 2 blank lines
            lines.insert(line_num - 1, "\n")
            lines.insert(line_num - 1, "\n")

        with open(file_path, "w") as f:
            f.writelines(lines)

        return {"action": "fix_syntax_error", "status": "pass"}
    except Exception as e:
        return {
            "action": "fix_syntax_error",
            "status": "fail",
            "error": f"Error fixing syntax: {e}",
        }
