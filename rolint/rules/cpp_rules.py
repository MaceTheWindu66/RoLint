def walk(node, source_code:str, symbol_table: dict, declared_table: dict, used_table: dict, is_global_var) -> list[dict]:

    violations = []

    # Check for banned functions including new and delete
    if node.type == "call_expression":
        violations += check_banned_funcs(node, source_code)
    elif node.type == "new_expression":
        violations.append({
            "line": node.start_point[0] + 1,
            "function": "new",
            "message": "Usage of 'new' is banned. Use static or stack allocation instead."
        })
    elif node.type == "delete_expression":
        violations.append({
            "line": node.start_point[0] + 1,
            "function": "delete",
            "message": "Usage of 'delete' is banned. Use RAII or static allocation instead."
        })
    elif node.type == "switch_statement":
        violations += check_switch_statement(node, source_code)
 
   

    for child in node.children:
        violations += walk(child, source_code, symbol_table, declared_table, used_table, is_global_var)
        

    return violations

def check_banned_funcs(node, source_code: str) -> list[dict]:

    banned_functions = {
        "malloc", "calloc", "realloc", "free",
        "printf", "sprintf", "scanf", "gets", "fgets",
        "rand", "srand", "time", "clock", "gettimeofday",
        "system", "fork", "exec", "exit",
        "va_start", "va_arg", "va_end",
        "cin", "cout", "cerr"
    }

    violations = []

    function_node = node.child_by_field_name('function')
    if function_node is not None:
        name = source_code[function_node.start_byte:function_node.end_byte].decode("utf-8")

        if '::' in name:
            name = name.split('::')[-1]
        
        
        if name in banned_functions:
            violations.append({
                "line": node.start_point[0] + 1,
                "function": name,
                "message": f"Usage of function '{name}' is banned. Please use safer alternative."
            })
    return violations

def check_switch_statement(node, source_code: str) -> list[dict]:

    """
    Check to ensure switch statements have no implicit fallthroughs and ensure existence of default case
    """
    violations = []
    has_default = False
    in_case_block = False
    has_fall = False
    # Get the compound_statement (the body of the switch)
    body = node.child_by_field_name("body")

    if body is None:
        return violations

    def walk_switch_subtree(n):

        nonlocal has_default
        nonlocal in_case_block
        nonlocal violations
        nonlocal has_fall
        
        if n.type == "case":
            if in_case_block and not has_fall:
                violations.append({
                    "line": n.start_point[0] + 1,
                    "message": "Switch case statement has implicit fallthrough. Add 'break;', 'return;', or '[[fallthrough]]'"
                })
            in_case_block = True
            has_fall = False

        if n.type == "break" or n.type == "return":
            has_fall = True
        if n.type == "continue":
            violations.append({
                "line": n.start_point[0] + 1,
                "message": "Use of 'continue' is banned."
            })

        if n.type == "default":
            has_default = True

        for child in n.children:
            walk_switch_subtree(child)

    
    walk_switch_subtree(body)

    if not has_default:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": "Switch statement missing 'default' case."
        })

    return violations

