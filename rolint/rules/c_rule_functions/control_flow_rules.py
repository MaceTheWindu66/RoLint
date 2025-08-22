## ---------------------------------------- Control Flow Safety Rules ----------------------------------------------------

#Ban unsafe switch statement practices
def check_switch_statement(node, source_code: str) -> list[dict]:
    violations = []

    has_default = False

    for child in node.named_children:
        if child.type == "default_label":
            has_default = True

        def walk_switch_subtree(n):
            nonlocal has_default, violations

            if n.type == "default_label":
                has_default = True

            elif n.type in {"break_statement", "continue_statement"}:
                violations += check_break_continue_in_switch(n, source_code)

            for child in n.children:
                walk_switch_subtree(child)

    walk_switch_subtree(node)

    # Check for fallthrough
    children = [child for child in node.child_by_field_name("body").children if child.type not in {'{', '}'}]
    current_label = None
    current_block = []

    for child in children:
        if child.type in {"case_label", "default_label"}:
            if current_label is not None:
                if not block_has_terminator_or_fallthrough_comment(current_block, source_code):
                    violations.append({
                        "line": current_label.start_point[0] + 1,
                        "message": f"Case '{source_code[current_label.start_byte:current_label.end_byte].decode('utf-8').strip()}' falls through implicitly. Add 'break;', 'return;', or comment like '/* fallthrough */'."
                    })
            current_label = child
            current_block = []
        else:
            current_block.append(child)

    if not has_default:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": "Switch statement missing 'default' case."
        })

    return violations

# Check to make sure we are not using break or continue in standalone switch cases. danger of undefined logic
def check_break_continue_in_switch(node, source_code: str) -> list[dict]:
    violations = []
    current = node.parent

    # Find enclosing control structures
    inside_loop = False
    inside_switch = False

    while current:
        if current.type in {"for_statement", "while_statement", "do_statement"}:
            inside_loop = True
        if current.type == "switch_statement":
            inside_switch = True
            break
        current = current.parent
    if node.type == "break_statement":
        # 'break' is allowed in switch and loop — do not warn
        pass

    return violations


# Helper function to detect fallthrough comment to allow for fallthrough
def block_has_terminator_or_fallthrough_comment(stmts, source_code: str) -> bool:
    for stmt in reversed(stmts):
        text = source_code[stmt.start_byte:stmt.end_byte].decode("utf-8").strip()

        if stmt.type in {"break_statement", "return_statement", "goto_statement", "throw_statement"}:
            return True
        if "fallthrough" in text.lower():
            return True
        if stmt.type != "comment":
            break  # hit a code statement that's not a terminator
    return False


# Ban Recursion (called outside of walk function in main)
def check_recursion(root_node, source_code: bytes) -> list[dict]:
    from rolint.rules.func_analysis_c import (
        collect_function_definitions,
        build_call_graph,
        detect_recursive_functions
    )

    violations = []
    source_str = source_code.decode("utf-8")

    functions = collect_function_definitions(root_node, source_code)
    call_graph = build_call_graph(functions, source_code)
    recursive_funcs = detect_recursive_functions(call_graph)

    for name in recursive_funcs:
        body = functions.get(name)
        if body:
            violations.append({
                "line": body.start_point[0] + 1,
                "message": f"Recursive function '{name}' is banned. Use an iterative alternative."
            })

    return violations