"""
    All C Rules will be encoded in this script here. This will consist of a set of banned functions,
    unsafe practices, etc.
"""

#Wanna keep this in O(nlogn) time at max (traversing the tree) Recursively walk the tree to find any violations..
def walk(node, source_code:str, symbol_table: dict, declared_table: dict, used_table: dict, is_global_var) -> list[dict]:

    violations = []

    if node.type == "call_expression":
        #Check expression call to see if function is banned
        violations += check_banned_functions(node, source_code)
        
        #Check for side effects in function call
        violations += check_side_effects_in_func_call(node, source_code)

    elif node.type == "declaration":  

        if is_global_var:
            violations += check_global(node, source_code)

        #Check declarations rules (multiple conversions, no initialization)  
        violations += check_declaration(node, source_code)


        #Check type conversions
        violations += check_implicit_conversion_in_declaration(node, source_code, symbol_table)

        # Track declared vars
        for child in node.named_children:
            if child.type == "init_declarator":
                ident = child.child_by_field_name("declarator")
                if ident and ident.type == "identifier":
                    name = source_code[ident.start_byte:ident.end_byte].decode("utf-8").strip()
                    declared_table["variables"][name] = node.start_point[0] + 1

    elif node.type == "assignment_expression":
        violations += check_implicit_conversion_in_assignment(node, source_code, symbol_table)

    elif node.type == "cast_expression":
        violations += check_casting(node, source_code, symbol_table)
        violations += check_narrowing_casts(node, source_code, symbol_table)
    
    elif node.type == "goto_statement":
        #Specifically banning goto statements
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Usage of 'goto' is banned. Please use structured control flow logic."
        })
    
    elif node.type == "switch_statement":
        violations += check_switch_statement(node, source_code)
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


    for child in node.children:
        violations += walk(child, source_code, symbol_table, declared_table, used_table, is_global_var)
        

    return violations



## ------------------------------------ Library and Language Use Rules -----------------------------------------

# Check if a function call is banned (strcpy, gets, etc)
def check_banned_functions(node, source_code: str) -> list[dict]:

    """
    Function checks each node for a function identifier and ensures the function name
    does not match any of the banned functions from the c standard library.
    Returns: list[dict] of violations which include a line, function name, and a message
    """

    banned_functions = {
        "gets", "strcpy", "strncpy", "printf", "sprintf", "vsprintf",
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

## ------------------------------------- Function / Variable Use Rules -----------------------------------------

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



## ------------------------------------------- Type Safety Rules ------------------------------------------------

#Check to ensure there are no dangerous type conversions
def check_implicit_conversion_in_declaration(node, source_code: str, symbol_table: dict) -> list[dict]:
    violations = []

    if node.type != "declaration":
        return violations

    type_node = node.child_by_field_name("type")
    if not type_node:
        return violations

    declared_type = source_code[type_node.start_byte:type_node.end_byte].decode("utf-8").strip()

    for child in node.named_children:
        if child.type != "init_declarator":
            continue

        var_node = child.child_by_field_name("declarator")
        value_node = child.child_by_field_name("value")

        if var_node and var_node.type == "pointer_declarator":
            var_node = var_node.child_by_field_name("declarator")

        if var_node and var_node.type == "identifier":
            var_name = source_code[var_node.start_byte:var_node.end_byte].decode("utf-8").strip()
            symbol_table[var_name] = declared_type  # Register variable type

            if value_node:
                value_text = source_code[value_node.start_byte:value_node.end_byte].decode("utf-8").strip()

                # Detect float literal assigned to int/char
                if declared_type in {"int", "short", "char"} and "." in value_text:
                    violations.append({
                        "line": node.start_point[0] + 1,
                        "message": f"Implicit conversion from float literal to '{declared_type}' in declaration of '{var_name}' may lose precision."
                    })

                # Check overflow risk in char assignment
                if declared_type == "char":
                    try:
                        val = int(value_text, 0)
                        if val > 127 or val < -128:
                            violations.append({
                                "line": node.start_point[0] + 1,
                                "message": f"Value {val} may overflow 'char' in declaration of '{var_name}'."
                            })
                    except ValueError:
                        pass

    return violations

#Check for implicit type conversion when assigning new values to integers
def check_implicit_conversion_in_assignment(node, source_code: str, symbol_table: dict) -> list[dict]:

    #conversion table for banned conversions
    conversion_table = {
    "double": ["float", "int", "short", "char"],
    "float":  ["int", "short", "char"],
    "long":   ["int", "short", "char"],
    "int":    ["short", "char"],
    "short":  ["char"]
    }


    violations = []

    if node.type != "assignment_expression":
        return violations

    left = node.child_by_field_name("left")
    right = node.child_by_field_name("right")

    if left is None or right is None:
        return violations

    left_name = source_code[left.start_byte:left.end_byte].decode("utf-8").strip()
    right_text = source_code[right.start_byte:right.end_byte].decode("utf-8").strip()

    r_type = None
    declared_type = symbol_table.get(left_name)

    
    if declared_type:
        if right.type == "identifier":
            r_type = symbol_table.get(right_text)
        elif "." in right_text:
            r_type = "float"
        elif right_text.isdigit():
            right_text = "int"

        #Check for int to float conversions
        if declared_type in {"int", "short", "char"} and r_type == "float":
            violations.append({
                "line": node.start_point[0] + 1,
                "message": f"Type mismatch or implicit conversion from float literal to '{declared_type}' in assignment to '{left_name}' may lose precision."
            })
        #Check for declaring float to int value (float x = 3)
        elif declared_type == "float" and r_type in {"int", "short", "char"}:
            print("WARNING: Declaring float as integer. Proceed with caution.")
        #Check to ensure no narrowing / data loss conversion
        elif declared_type in conversion_table and r_type in conversion_table[declared_type]:
            violations.append({
                "line": node.start_point[0] + 1,
                "message": f"Implicit narrowing conversion from '{r_type}' to '{declared_type}' in assignment to '{left_name}' may lose precision."
            })

        if declared_type == "char":
            try:
                val = int(right_text, 0)
                if val > 127 or val < -128:
                    violations.append({
                        "line": node.start_point[0] + 1,
                        "message": f"Value {val} may overflow 'char' in assignment to '{left_name}'."
                    })
            except ValueError:
                pass
        

    return violations

#Casting between pointers and arithmetic types banned.
def check_casting(node, source_code:str, symbol_table:dict) -> list[dict]:

    violations = []

    if node.type != "cast_expression":
        return violations

    type_node = node.child_by_field_name("type")
    value_node = node.child_by_field_name("value")
    if not type_node or not value_node:
        return violations
    
    cast_text = source_code[type_node.start_byte:type_node.end_byte].decode("utf-8").strip()

    is_to_ptr = "*" in cast_text
    is_to_arithmetic = any(t in cast_text for t in {"int", "float", "double", "long", "short", "char"})

    if value_node.type == "identifier":
        var_name = source_code[value_node.start_byte:value_node.end_byte].decode("utf-8").strip()
        cast_from = symbol_table.get(var_name, "")
    else:
        # Infer from literal or expression
        value_text = source_code[value_node.start_byte:value_node.end_byte].decode("utf-8").strip()
        if "." in value_text:
            cast_from = "float"
        elif value_text.isdigit():
            cast_from = "int"
        elif value_node.type.endswith("literal"):
            cast_from = value_node.type
        else:
            cast_from = "unknown"

    is_from_ptr = "*" in cast_from
    is_from_arith = any(t in cast_from for t in {"int", "float", "double", "char", "short", "long"})

    # Ban pointer <-> arithmetic casts
    if (is_to_ptr and is_from_arith) or (is_from_ptr and is_to_arithmetic):
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Cast from '{cast_from}' to '{cast_text}' between pointer and arithmetic type is banned."
        })

    return violations

#Ban narrowing casts (float casted to int, long casted to short, etc)
def check_narrowing_casts(node, source_code: str, symbol_table: dict) -> list[dict]:
    violations = []

    if node.type != "cast_expression":
        return violations

    type_node = node.child_by_field_name("type")
    value_node = node.child_by_field_name("value")

    if not type_node or not value_node:
        return violations

    # Extract target type (cast-to)
    cast_to = source_code[type_node.start_byte:type_node.end_byte].decode("utf-8").strip()

    # Infer cast-from type
    cast_from = "unknown"

    if value_node.type == "identifier":
        ident_name = source_code[value_node.start_byte:value_node.end_byte].decode("utf-8").strip()
        cast_from = symbol_table.get(ident_name, "unknown")

    else:
        value_text = source_code[value_node.start_byte:value_node.end_byte].decode("utf-8").strip()

        if "." in value_text:
            cast_from = "double" if "e" in value_text.lower() else "float"
        elif value_text.isdigit():
            cast_from = "int"
        elif value_node.type.endswith("literal"):
            cast_from = value_node.type

    # Normalize cast types
    cast_from = cast_from.lower().strip()
    cast_to = cast_to.lower().strip()

    # Define narrowing hierarchy
    narrowing_table = {
        "double": ["float", "long", "int", "short", "char"],
        "float":  ["int", "short", "char"],
        "long":   ["int", "short", "char"],
        "int":    ["short", "char"],
        "short":  ["char"]
    }

    if cast_from in narrowing_table and cast_to in narrowing_table[cast_from]:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Narrowing cast from '{cast_from}' to '{cast_to}' may lose precision or range."
        })

    return violations
 
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

    # TODO: add fallthrough detection here

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

    while current:
        if current.type in {"for_statement", "while_statement", "do_statement"}:
            # Found loop first – allow
            return violations

        if current.type == "switch_statement":
            # Found switch before loop – check if *another* loop is above this
            loop_above = current.parent
            while loop_above:
                if loop_above.type in {"for_statement", "while_statement", "do_statement"}:
                    return violations  # This switch is inside a loop – allow
                loop_above = loop_above.parent

            # If no loop found enclosing switch -> banned
            violations.append({
                "line": node.start_point[0] + 1,
                "message": f"Usage of '{node.type.replace('_statement', '')}' inside a switch statement is banned. Use explicit control flow instead."
            })
            return violations

        current = current.parent

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

## ------------------------------------------------------------------------------------------------------------------------



## Control Flow Safety Rules
# - No Goto <-- DONE
# - no break; continue inside switch statements <-- DONE
# - all switch statements must have a default <-- DONE
# - No recursion <-- DONE

## Memory Safety
# - No malloc, calloc, or free statements (dynamic memory allocation not allowed) <-- DONE 
# - No use of NULL without type context 
# - No object definitions in header files 

## Function and Variable Use 
# - No unused variables / functions <-- DONE
# - No global variables unless const <-- DONE
# - No side effects in function arguments <-- DONE  

