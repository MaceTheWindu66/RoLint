import re
from typing import Optional, Tuple



PRIMITIVE = {"char","short","int","long","float","double","bool","_Bool"}

def _slice(src: bytes, n) -> str:
    return src[n.start_byte:n.end_byte].decode("utf-8", errors="ignore").strip()

def _unwrap_parens(n):
    while n and n.type == "parenthesized_expression":
        inner = n.child_by_field_name("expression")
        n = inner or (n.children[1] if len(n.children) >= 2 else n)
    return n

def _strip_quals(t: str) -> str:
    return re.sub(r"\b(const|volatile|restrict|signed|register)\b", "", t).strip()

def _normalize_type(t: Optional[str], typedefs: Optional[dict]=None):
    """
    Returns a tuple: (kind, struct_name, ptr_depth)
      kind: one of PRIMITIVE or 'struct' or None
      struct_name: e.g. 'S' if kind=='struct' else None
      ptr_depth: number of '*'
    """
    if not t:
        return None, None, 0
    if typedefs and t in typedefs:
        t = typedefs[t]
    t = _strip_quals(t)
    ptr_depth = t.count("*")
    base = t.replace("*", "").strip()
    if base.startswith("struct "):
        return "struct", base.split(None, 1)[1], ptr_depth
    return base, None, ptr_depth

def _infer_literal_type(node, src: bytes) -> Optional[str]:
    # float literals: contain '.' or exponent (dec/hex); 'f'/'F' suffix ⇒ float else double
    if node.type == "number_literal":
        t = _slice(src, node)
        if any(ch in t for ch in ('.','e','E','p','P')):
            return "float" if re.search(r"[fF]$", t) else "double"
        return "int"
    if node.type == "char_literal":
        return "char"
    return None

def _is_member_access(n) -> bool:
    # TS C uses 'field_expression' for both '.' and '->'. Some grammars also expose 'arrow_expression'.
    return n.type in {"field_expression", "arrow_expression"}

def _field_parts(node):
    # Return (base_expr_node, field_identifier_node)
    base = node.child_by_field_name("argument") or node.child_by_field_name("object")
    if base is None and node.children:
        base = node.children[0]
    field = node.child_by_field_name("field")
    if field is None:
        for c in reversed(node.children):
            if c.type in ("field_identifier","property_identifier","identifier"):
                field = c
                break
    return base, field

def resolve_struct_field_type(expr_node, src: bytes, symtab: dict, struct_table: dict, typedefs: Optional[dict]=None) -> Optional[str]:
    """
    For a.b / a->b return the declared field type string, or None if unknown.
    """
    if not _is_member_access(expr_node):
        return None
    base, field = _field_parts(expr_node)
    if not base or not field:
        return None
    base_t = resolve_expr_type(base, src, symtab, struct_table, typedefs)
    kind, sname, ptr = _normalize_type(base_t, typedefs)
    if kind != "struct" or not sname:
        return None
    # (optional) sanity: '.' expects ptr==0, '->' expects ptr>=1
    field_name = _slice(src, field)
    return struct_table.get(sname, {}).get(field_name)

def resolve_expr_type(node, src: bytes, symtab: dict, struct_table: dict, typedefs: Optional[dict]=None) -> Optional[str]:
    """
    Try to determine the type string of an expression: identifier, member, or literal.
    Returns a textual type (e.g., 'int', 'double', 'struct S', 'struct S *', etc.) or None.
    """
    node = _unwrap_parens(node)
    if node.type == "identifier":
        return symtab.get(_slice(src, node))
    if _is_member_access(node):
        return resolve_struct_field_type(node, src, symtab, struct_table, typedefs)
    lit = _infer_literal_type(node, src)
    if lit:
        return lit
    # (extend later: unary, binary, calls, array subscripts)
    return None

def compose_decl_type(
    base_type_text: str,
    declarator_node,
    source_code: bytes,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (var_name, full_type) from a single declarator (handles pointer layers).
    Example outputs: ('a', 'int'), ('p', 'struct S *'), ('pp', 'int **')
    """
    ptr = 0
    d = declarator_node

    # Walk down through pointer/array/function wrappers to reach the identifier.
    while d:
        t = d.type
        if t == "pointer_declarator":
            ptr += 1
            d = d.child_by_field_name("declarator") or (d.children[-1] if d.children else None)
            continue
        if t in {"array_declarator", "function_declarator"}:
            # You can record array/function info later if you want; for now just descend.
            d = d.child_by_field_name("declarator") or (d.children[0] if d.children else None)
            continue
        if t == "parenthesized_declarator":
            d = d.child_by_field_name("declarator") or (d.children[1] if len(d.children) > 1 else None)
            continue
        break

    if not d or d.type != "identifier":
        return None, None

    name = _slice(source_code, d)
    full = (base_type_text + " " + ("*" * ptr)).strip()
    return name, full


## ------------------------------------------- Type Safety Rules ------------------------------------------------

#Check to ensure there are no dangerous type conversions
def check_implicit_conversion_in_declaration(node, source_code: bytes, symbol_table: dict,
                                             struct_table: dict, typedefs: Optional[dict]=None) -> list[dict]:
    violations = []
    if node.type != "declaration":
        return violations

    type_node = node.child_by_field_name("type")
    if not type_node:
        return violations
    base_type = _slice(source_code, type_node)

    # Forward-decl like `struct MSG;` has no init_declarators
    has_declarators = any(ch.type == "init_declarator" for ch in node.named_children)

    for child in node.named_children:
        if child.type != "init_declarator":
            continue

        decl = child.child_by_field_name("declarator")
        value_node = child.child_by_field_name("value")
        if not decl:
            continue

        # derive var name + pointer depth for this declarator
        var_name = None
        ptr = 0
        d = decl
        while d and d.type == "pointer_declarator":
            ptr += 1
            d = d.child_by_field_name("declarator") or (d.children[-1] if d.children else None)
        if d and d.type == "identifier":
            var_name = _slice(source_code, d)
        if not var_name:
            continue

        declared_type_full = (base_type + " " + ("*" * ptr)).strip()
        symbol_table[var_name] = declared_type_full  # per-variable, not just base

        # initializer checks (only for simple numeric literals or resolvable struct fields)
        if value_node:
            rhs_type = resolve_expr_type(value_node, source_code, symbol_table, struct_table, typedefs)
            # only compare when known
            if rhs_type:
                lhs_kind, _, _ = _normalize_type(declared_type_full, typedefs)
                rhs_kind, _, _ = _normalize_type(rhs_type, typedefs)

                if lhs_kind in {"int","short","char"} and rhs_kind in {"float","double"}:
                    violations.append({
                        "line": node.start_point[0] + 1,
                        "message": f"Implicit conversion from {rhs_kind} literal to '{lhs_kind}' in declaration of '{var_name}' may lose precision."
                    })

                if lhs_kind == "char" and value_node.type == "number_literal":
                    txt = _slice(source_code, value_node)
                    if not any(ch in txt.lower() for ch in ('.','e','p')):
                        try:
                            val = int(txt, 0)
                            if val > 127 or val < -128:
                                violations.append({
                                    "line": node.start_point[0] + 1,
                                    "message": f"Value {val} may overflow 'char' in declaration of '{var_name}'."
                                })
                        except ValueError:
                            pass

    return violations


#Check for implicit type conversion when assigning new values to integers
def check_implicit_conversion_in_assignment(node, source_code: bytes, symbol_table: dict,
                                            struct_table: dict, typedefs: Optional[dict]=None) -> list[dict]:
    conversion_table = {
        "double": ["float", "long", "int", "short", "char"],
        "float":  ["int", "short", "char"],
        "long":   ["int", "short", "char"],
        "int":    ["short", "char"],
        "short":  ["char"]
    }
    violations = []
    if node.type != "assignment_expression":
        return violations

    left = _unwrap_parens(node.child_by_field_name("left"))
    right = _unwrap_parens(node.child_by_field_name("right"))
    if not left or not right:
        return violations

    # LHS type: identifier or struct field
    lhs_type = None
    lhs_name = _slice(source_code, left)
    if left.type == "identifier":
        lhs_type = symbol_table.get(lhs_name)
    elif _is_member_access(left):
        lhs_type = resolve_struct_field_type(left, source_code, symbol_table, struct_table, typedefs)
    else:
        return violations

    if not lhs_type:
        return violations

    rhs_type = resolve_expr_type(right, source_code, symbol_table, struct_table, typedefs)

    
    if not rhs_type:
        return violations

    lkind, _, _ = _normalize_type(lhs_type, typedefs)
    rkind, _, _ = _normalize_type(rhs_type, typedefs)

    # float/double → int/short/char
    if lkind in {"int","short","char"} and rkind in {"float","double"}:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Type mismatch or implicit conversion from {rkind} to '{lkind}' in assignment to '{lhs_name}' may lose precision."
        })
    # general narrowing (e.g., long → short)
    elif lkind in conversion_table and rkind in conversion_table[lkind]:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Implicit narrowing conversion from '{rkind}' to '{lkind}' in assignment to '{lhs_name}' may lose precision."
        })

    if lkind == "char" and right.type == "number_literal":
        txt = _slice(source_code, right)
        if not any(ch in txt.lower() for ch in ('.','e','p')):
            try:
                val = int(txt, 0)
                if val > 127 or val < -128:
                    violations.append({
                        "line": node.start_point[0] + 1,
                        "message": f"Value {val} may overflow 'char' in assignment to '{lhs_name}'."
                    })
            except ValueError:
                pass

    return violations

#Casting between pointers and arithmetic types banned.
def check_casting(node, source_code: bytes, symbol_table: dict,
                  struct_table: dict, typedefs: Optional[dict]=None) -> list[dict]:
    violations = []
    if node.type != "cast_expression":
        return violations

    type_node = node.child_by_field_name("type")
    value_node = node.child_by_field_name("value")
    if not type_node or not value_node:
        return violations

    cast_to_text = _slice(source_code, type_node)
    to_kind, to_struct, to_ptr = _normalize_type(cast_to_text, typedefs)


    cast_from_text = resolve_expr_type(value_node, source_code, symbol_table, struct_table, typedefs)
    from_kind, from_struct, from_ptr = _normalize_type(cast_from_text, typedefs)


    if to_kind is None and from_kind is None:
        return violations

    # Pointer <-> arithmetic is banned
    to_is_ptr = to_ptr > 0
    from_is_ptr = from_ptr > 0
    to_is_arith = to_kind in PRIMITIVE
    from_is_arith = from_kind in PRIMITIVE

    # Struct value casts (not pointers) are invalid/banned in practice
    to_is_struct_val = (to_kind == "struct" and to_ptr == 0)
    from_is_struct_val = (from_kind == "struct" and from_ptr == 0)

    if (to_is_ptr and from_is_arith) or (from_is_ptr and to_is_arith):
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Cast from '{cast_from_text}' to '{cast_to_text}' between pointer and arithmetic type is banned."
        })
    elif to_is_struct_val or from_is_struct_val:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Cast involving struct value type is banned: '{cast_from_text}' → '{cast_to_text}'."
        })

    return violations

#Ban narrowing casts (float casted to int, long casted to short, etc)
def check_narrowing_casts(node, source_code: bytes, symbol_table: dict,
                          struct_table: dict, typedefs: Optional[dict]=None) -> list[dict]:
    violations = []
    if node.type != "cast_expression":
        return violations

    type_node = node.child_by_field_name("type")
    value_node = node.child_by_field_name("value")
    if not type_node or not value_node:
        return violations

    cast_to_text = _slice(source_code, type_node)
    to_kind, _, to_ptr = _normalize_type(cast_to_text, typedefs)

    cast_from_text = resolve_expr_type(value_node, source_code, symbol_table, struct_table, typedefs)
    from_kind, _, from_ptr = _normalize_type(cast_from_text, typedefs)

    # Only arithmetic (non-pointers) participate in narrowing here
    if to_kind not in PRIMITIVE or from_kind not in PRIMITIVE or to_ptr or from_ptr:
        return violations

    narrowing = {
        "double": ["float", "long", "int", "short", "char"],
        "float":  ["int", "short", "char"],
        "long":   ["int", "short", "char"],
        "int":    ["short", "char"],
        "short":  ["char"]
    }

    if from_kind in narrowing and to_kind in narrowing[from_kind]:
        violations.append({
            "line": node.start_point[0] + 1,
            "message": f"Narrowing cast from '{from_kind}' to '{to_kind}' may lose precision or range."
        })

    return violations