
def check_banned_functions(node, source_code: str) -> list[dict]:

    """
    Function checks each node for a function identifier and ensures the function name
    does not match any of the banned functions from the c standard library.
    Returns: list[dict] of violations which include a line, function name, and a message
    """

    banned_functions = {
        "gets", "strcpy", "printf", "sprintf", "vsprintf",
        "strcat", "strncat", "scanf", "sscanf", "fscanf",
        "strtok", "atoi", "atol", "atof", "atoll", "setjmp", "longjmp",
        "malloc", "calloc", "free", "realloc"
    }

    violations = []

    
   
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
                "message": f"Usage of function '{func_name}' is banned. Please use safer alternative."
            })

    return violations
