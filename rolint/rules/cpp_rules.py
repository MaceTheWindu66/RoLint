


def walk(node, source_code:str, symbol_table: dict, declared_table: dict, used_table: dict, is_global_var, ignored_lines, ignored_blocks) -> list[dict]:

    violations = []

    ignored_line_nums  = {il["line"] - 1 for il in ignored_lines}
    ignored_block_nums = {ib["line"] - 1 for ib in ignored_blocks}

    if node.start_point[0] in ignored_block_nums:
        
        return violations  

    if node.start_point[0] not in ignored_line_nums:
        # Check for banned functions including new and delete
        if node.type == "call_expression":
            violations += check_banned_funcs(node, source_code)


        # Ban delete and new
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

        #Check for misuse of switch statements
        elif node.type == "switch_statement":
            violations += check_switch_statement(node, source_code)

        #Ban goto
        elif node.type == "goto":
            violations.append({
                "line": node.start_point[0] + 1,
                "message": "Usage of 'goto' and any uncontrolled jumps are banned."
            })
        
        #Ban function-like macros
        elif node.type == "preproc_function_def":
            violations.append({
                "line": node.start_point[0] + 1,
                "message": "Definition of function-like macros are banned. Consider using 'inline'."
            })
    

        for child in node.children:
            violations += walk(child, source_code, symbol_table, declared_table, used_table, is_global_var,
                               ignored_lines, ignored_blocks)
            

    return violations


# CHECKS


def check_banned_funcs(node, source_code: str) -> list[dict]:
    """
    Ensures function call is not banned. Unsafe functions are defined as those who either dynamically allocate memory or
    have the potential to cause overflow. 
    """

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
    violations = []
    has_default = False

    body = node.child_by_field_name("body")
    if body is None:
        return violations

    # Flatten to look at named children (statements in body)
    children = body.named_children
    last_case = None
    case_block_has_exit = False

    for i, child in enumerate(children):
        if child.type == "default_label":
            has_default = True

        elif child.type == "case_label":
            if last_case is not None and not case_block_has_exit:
                # If previous case block ended with no break/return
                violations.append({
                    "line": child.start_point[0] + 1,
                    "message": "Switch case statement has implicit fallthrough. Add 'break;', 'return;', or '[[fallthrough]]'"
                })
            last_case = child
            case_block_has_exit = False

        elif child.type in {"break_statement", "return_statement", "throw_statement"}:
            case_block_has_exit = True

        elif child.type == "continue_statement":
            violations.append({
                "line": child.start_point[0] + 1,
                "message": "Use of 'continue' is banned."
            })

    if not has_default:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": "Switch statement missing 'default' case."
        })

    return violations

