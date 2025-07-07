"""
    All C Rules will be encoded in this script here. This will consist of a set of banned functions,
    unsafe practices, etc.
"""

#Wanna keep this in O(nlogn) time at max (traversing the tree) Recursively walk the tree to find any violations..
def walk(node, source_code:str, symbol_table: dict) -> list[dict]:

    violations = []

    if node.type == "call_expression":

        #Check expression call to see if function is banned
        violations += check_banned_functions(node, source_code)

    elif node.type == "declaration":  
        #Check declarations rules (multiple conversions, no initialization)  
        violations += check_declaration(node, source_code)

        #Check type conversions
        violations += check_implicit_conversion_in_declaration(node, source_code, symbol_table)

    elif node.type == "assignment_expression":
        violations += check_implicit_conversion_in_assignment(node, source_code, symbol_table)

    elif node.type == "cast_expression":
        violations += check_casting(node, source_code, symbol_table)
        violations += check_narrowing_casts(node, source_code, symbol_table)


    for child in node.children:
        violations += walk(child, source_code, symbol_table)

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
 