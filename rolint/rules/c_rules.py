"""
    All C Rules will be encoded in this script here. This will consist of a set of banned functions,
    unsafe practices, etc.
"""

import tree_sitter

def check_banned_functions(tree, source_code: str) -> list[dict]:
    banned_functions = {
        "gets", "strcpy", "strncpy", "printf", "sprintf", "vsprintf",
        "strcat", "strncat", "scanf", "sscanf", "fscanf",
        "strtok", "atoi", "atol", "atof", "atoll"
    }

    violations = []

    def walk(node):
        if node.type == "call_expression":
            # Try the standard way
            func_node = node.child_by_field_name("function")

            # If the field is missing, try fallback
            if func_node is None:
                # Try to find the first identifier before the argument list
                for child in node.children:
                    if child.type == "identifier":
                        func_node = child
                        break

            if func_node and func_node.type == "identifier":
                func_name = source_code[func_node.start_byte:func_node.end_byte].decode("utf-8")
                if func_name in banned_functions:
                    violations.append({
                        "line": node.start_point[0] + 1,
                        "function": func_name,
                        "message": f"Usage of banned function '{func_name}' is banned. Please use safer alternative."
                    })

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return violations

