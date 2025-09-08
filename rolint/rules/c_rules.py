from .c_rule_functions.check_banned_funcs import check_banned_functions
from .c_rule_functions import function_and_vars_use
from .c_rule_functions import control_flow_rules
from .c_rule_functions import type_safety

"""
    All C Rules will be encoded in this script here. This will consist of a set of banned functions,
    unsafe practices, etc.
"""

def walk(node, source_code:str, symbol_table: dict, declared_table: dict, used_table: dict, struct_table, is_global_var, ignored_lines, ignored_blocks) -> list[dict]:

    ignored_line_nums  = {il["line"] - 1 for il in ignored_lines}
    ignored_block_nums = {ib["line"] - 1 for ib in ignored_blocks}
    
    violations = []

    if (node.start_point[0] in ignored_block_nums):
        
        return violations  

    if node.start_point[0] in ignored_line_nums:
        return violations
    else:
        if node.type == "call_expression":
            #Check expression call to see if function is banned
            violations += check_banned_functions(node, source_code)
            
            #Check for side effects in function call
            violations += function_and_vars_use.check_side_effects_in_func_call(node, source_code)

        elif node.type == "declaration":  

            if is_global_var:
                violations += function_and_vars_use.check_global(node, source_code)

            #Check declarations rules (multiple conversions, no initialization)  
            violations += function_and_vars_use.check_declaration(node, source_code)


            #Check type conversions
            violations += type_safety.check_implicit_conversion_in_declaration(node, source_code, symbol_table, struct_table)

            # Track declared vars
            for child in node.named_children:
                if child.type == "init_declarator":
                    ident = child.child_by_field_name("declarator")
                    if ident and ident.type == "identifier":
                        name = source_code[ident.start_byte:ident.end_byte].decode("utf-8").strip()
                        declared_table["variables"][name] = node.start_point[0] + 1

        elif node.type == "assignment_expression":
            violations += type_safety.check_implicit_conversion_in_assignment(node, source_code, symbol_table, struct_table)

        elif node.type == "cast_expression":
            violations += type_safety.check_casting(node, source_code, symbol_table, struct_table)
            violations += type_safety.check_narrowing_casts(node, source_code, symbol_table, struct_table)
        
        elif node.type == "continue_statement":
            violations.append({
                "line": node.start_point[0] + 1,
                "message": "Use of 'continue' is banned."
            })
        elif node.type == "goto_statement":
            #Specifically banning goto statements
            violations.append({
                "line": node.start_point[0] + 1,
                "message": "Usage of 'goto' is banned. Please use structured control flow logic."
            })
        
        elif node.type == "switch_statement":
            violations += control_flow_rules.check_switch_statement(node, source_code)
        elif node.type == "preproc_function_def":
            violations += check_function_like_macros(node, source_code)

        ##Checks for unused funcs or vars
        elif node.type == "function_definition":
            is_global_var = False
            func_node = node.child_by_field_name("declarator")
            if func_node:
                ident_node = func_node.child_by_field_name("declarator")
                if ident_node and ident_node.type == "identifier":
                    name = source_code[ident_node.start_byte:ident_node.end_byte].decode("utf-8").strip()
                    declared_table["functions"][name] = node.start_point[0] + 1

        elif node.type == "identifier":

            name = source_code[node.start_byte:node.end_byte].decode("utf-8").strip()

            # Only mark as used if not part of a declaration
            parent = node.parent
            if parent and parent.type != "init_declarator" and parent.type != "declaration":
                if name in declared_table["variables"]:
                    used_table["variables"].add(name)
                if name in declared_table["functions"]:
                    used_table["functions"].add(name) 

    if node.start_point[0] not in ignored_block_nums:
        for child in node.children:
            violations += walk(child, source_code, symbol_table, declared_table, used_table, struct_table, is_global_var, ignored_lines, ignored_blocks)
        

    return violations



## ------------------------------------- Function / Variable Use Rules -----------------------------------------



#Check for function like macros
def check_function_like_macros(node, source_code: str) -> list[dict]:
    violations = []

    name_node = node.child_by_field_name("name")
    if name_node:
        name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Function-like macro '{name}' detected. Usage of function-like macros is banned. Use inline functions instead."
        })

    return violations

 
## ----------------------------------------------- HEADER RULES -----------------------------------------------------------

# Ensure header guards
def check_header_guard(source_code: bytes, file_path: str) -> list[dict]:
    lines = source_code.splitlines()
    violations = []

    guard_macro = None

    # Look for #ifndef and matching #define in the first 10 lines
    for i, line in enumerate(lines):
        stripped = line.strip().decode("utf-8")  #  decode from bytes to str
        if stripped.startswith("#ifndef"):
            parts = stripped.split()
            if len(parts) == 2:
                guard_macro = parts[1]

        elif stripped.startswith("#define") and guard_macro:
            if guard_macro not in stripped:
                guard_macro = None  # Reset if mismatch
            else:
                break

    # Look for #endif near end
    has_endif = any(
        line.strip().decode("utf-8").startswith("#endif") for line in lines[-10:]
    )

    if not (guard_macro and has_endif):
        violations.append({
            "line": 1,
            "message": f"Header file '{file_path}' is missing proper include guards (#ifndef / #define / #endif)."
        })

    return violations


def check_object_definitions_in_header(tree, source_code: str) -> list[dict]:
    violations = []

    def is_function_declaration(node):
        return node.type == "function_declaration"

    def walk(n):
        nonlocal violations
        if n.type == "declaration":
            # Check if this is a definition (i.e., has init_declarator with value)
            for child in n.named_children:
                if child.type == "init_declarator":
                    value = child.child_by_field_name("value")
                    if value is not None:
                        ident = child.child_by_field_name("declarator")
                        if ident:
                            name = source_code[ident.start_byte:ident.end_byte].decode("utf-8")
                            violations.append({
                                "line": n.start_point[0] + 1,
                                "message": f"Object '{name}' defined in header file. Object definitions are banned in headers."
                            })
        for child in n.children:
            walk(child)

    walk(tree.root_node)
    return violations


# Check to make sure everything that is declared is used
def check_unused(declared_symbols, used_symbols):
    violations = []

    unused_vars = set(declared_symbols["variables"].keys()) - used_symbols["variables"]
    for name in unused_vars:
        line = declared_symbols["variables"][name]
        violations.append({
            "line": line,
            "message": f"Variable '{name}' declared but never used."
        })

    unused_funcs = set(declared_symbols["functions"].keys()) - used_symbols["functions"]
    for name in unused_funcs:
        line = declared_symbols["functions"][name]
        violations.append({
            "line": line,
            "message": f"Function '{name}' defined but never called."
        })

    return violations

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




## Control Flow Safety Rules
# - No Goto <-- DONE
# - no break; continue inside switch statements <-- DONE
# - all switch statements must have a default <-- DONE
# - No recursion <-- DONE

## Memory Safety
# - No malloc, calloc, or free statements (dynamic memory allocation not allowed) <-- DONE 
# - No use of NULL without type context 
# - No object definitions in header files <-- DONE

## Function and Variable Use 
# - No unused variables / functions <-- DONE
# - No global variables unless const <-- DONE
# - No side effects in function arguments <-- DONE  

