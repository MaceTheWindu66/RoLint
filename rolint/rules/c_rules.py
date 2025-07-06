"""
    All C Rules will be encoded in this script here. This will consist of a set of banned functions,
    unsafe practices, etc.
"""

#Wanna keep this in O(nlogn) time at max (traversing the tree) Recursively walk the tree to find any violations..
def walk(node, source_code:str) -> list[dict]:

    #Begin at the root. 

    violations = []

    if node.type == "call_expression":
        violations += check_banned_functions(node, source_code)
    elif node.type == "declaration":
        
        violations += check_declaration(node, source_code)

    for child in node.children:
        violations += walk(child, source_code)

    return violations


def check_banned_functions(node, source_code: str) -> list[dict]:

    """
    Function checks each node for a function identifier and ensures the function name
    does not match any of the banned functions from the c standard library.
    Returns: list[dict] of violations which include a line, function name, and a message
    """

    banned_functions = {
        "gets", "strcpy", "strncpy", "printf", "sprintf", "vsprintf",
        "strcat", "strncat", "scanf", "sscanf", "fscanf",
        "strtok", "atoi", "atol", "atof", "atoll"
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
                "message": f"Usage of banned function '{func_name}' is banned. Please use safer alternative."
            })

    return violations

#Check declaration function
def check_declaration(node, source_code: str) -> list[dict]:
    """
    Function to check variable declarations. Enforces two rules: multiple declarations on one line and unitialized variables.
    Returns a list of violations which includes a line, variable name, and a message.
    """


    violations = []

    if node.type != "declaration":
        return violations

    # Extract all relevant declarators
    declarators = [
        child for child in node.named_children
        if child.type in {"init_declarator", "identifier"}
    ]

    # Check for multiple variables declared
    if len(declarators) > 1:
        vars_declared = []
        for declared in declarators:
            if declared.type == "identifier":
                var_name = source_code[declared.start_byte:declared.end_byte].decode("utf-8").strip()
                vars_declared.append(var_name)
            elif declared.type == "init_declarator":
                ident = declared.child_by_field_name("declarator")
                if ident and ident.type == "pointer_declarator":
                    ident = ident.child_by_field_name("declarator")
                if ident and ident.type == "identifier":
                    var_name = source_code[ident.start_byte:ident.end_byte].decode("utf-8").strip()
                    vars_declared.append(var_name)
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Multiple variables declared in one statement: {', '.join(vars_declared)}. Please separate onto separate lines."
        })
        return violations  # Stop here if multiple declared

    # Check for initialization
    if len(declarators) == 1:
        declared = declarators[0]

        # raw identifier like `int a;` for uninitialized variables
        if declared.type == "identifier":
            var_name = source_code[declared.start_byte:declared.end_byte].decode("utf-8").strip()
            violations.append({
                "line": node.start_point[0] + 1,
                "message": f"Variable '{var_name}' declared without initialization."
            })
            return violations

        # Check to make sure the variable is initialized even if there is an init_declarator
        has_initializer = len(declared.named_children) > 1
        if not has_initializer:
            ident = declared.child_by_field_name("declarator")
            if ident and ident.type == "pointer_declarator":
                ident = ident.child_by_field_name("declarator")
            if ident and ident.type == "identifier":
                var_name = source_code[ident.start_byte:ident.end_byte].decode("utf-8").strip()
            else:
                var_name = "unknown"

            violations.append({
                "line": node.start_point[0] + 1,
                "message": f"Variable '{var_name}' declared without initialization."
            })

    return violations

