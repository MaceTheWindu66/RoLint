# Check if a global var is marked as a constant or volatile
def check_global(node, source_code: str) -> list[dict]:
    violations = []


    # Gather all modifier keywords to check for const or volatile
    modifiers = set()
    for child in node.children:
        if child.type == "type_qualifier" or child.type == "storage_class_specifier":
            qualifier = source_code[child.start_byte:child.end_byte].decode("utf-8")
            modifiers.add(qualifier)

    is_cleared = "const" in modifiers or "volatile" in modifiers or "static" in modifiers or "extern" in modifiers

    # If it doesn't have const or volatile, extract the node info and add to violations
    if not is_cleared:
        for child in node.named_children:
            ident = None
            if child.type == "init_declarator":
                ident = child.child_by_field_name("declarator")
            elif child.type == "array_declarator":
                ident = child.child_by_field_name("declarator")

            while ident and ident.type in {"pointer_declarator", "array_declarator"}:
                ident = ident.child_by_field_name("declarator")

            if ident and ident.type == "identifier":
                var_name = source_code[ident.start_byte:ident.end_byte].decode("utf-8")
                violations.append({
                    "line": node.start_point[0] + 1,
                    "message": f"Global variable '{var_name}' must be marked 'const', 'extern', 'static', or 'volatile'."
                })

    return violations

#Check declaration function (Functions and Variable use)
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

# Ban side effects in function calls (ex. printf(x++) or printf(getchar()) is unallowed)
def check_side_effects_in_func_call(node, source_code:str) -> list[dict]:
    violations = []

    #Functions that I will allow as I know they don't have side effects to data
    known_pure_functions = {"abs", "sqrt", "strlen", "toupper", "tolower"}

    args_node = node.child_by_field_name("arguments")
    if not args_node:
        return violations
    
    # Recursive walk through all node's children to ensure no side effects
    def contains_side_effects(n):
        if n.type in {"assignment_expression", "update_expression"}:
            return True
        elif n.type == "call_expression":
            func_name_node = n.child_by_field_name("function")
            if func_name_node:
                func_name = source_code[func_name_node.start_byte:func_name_node.end_byte].decode("utf-8")
                if func_name in known_pure_functions:
                    return False 
            return True
        for child in n.children:
            if contains_side_effects(child):
                return True
        return False
    
    for arg in args_node.named_children:
        if contains_side_effects(arg):
            func_node = node.child_by_field_name("function")
            func_name = source_code[func_node.start_byte:func_node.end_byte].decode("utf-8") if func_node else "unknown"
        
            violations.append({
                "line": func_node.start_point[0] + 1,
                "message": f"Side effect or function call in arguments for function call '{func_name}'."
            })


    return violations

