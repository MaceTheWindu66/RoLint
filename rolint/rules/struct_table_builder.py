"""
This file is to be used mainly for creating a global struct table between C files. This way, we can track 
structs defined in header files in the subsequent files in which they are used.
"""

def build_struct_table(node, source_code:str) -> list[dict]:

    """
        Walks the AST to build a table of tables essentially.
        {
            "StructName":
                {field1: type},
                {field2: type},
        }
    """
    struct_table = {}

    def walk(n):
        if n.type == "struct_specifier":
            name_node = n.child_by_field_name("name")
            if not name_node:
                return  # Skip unnamed structs

            struct_name = source_code[name_node.start_byte:name_node.end_byte].decode("utf-8")

            field_decls = {}
            for child in n.named_children:
                if child.type == "field_declaration_list":
                    for field in child.named_children:
                        if field.type == "field_declaration":
                            type_node = field.child_by_field_name("type")
                            decl_node = field.child_by_field_name("declarator")
                            if type_node and decl_node:
                                field_type = source_code[type_node.start_byte:type_node.end_byte].decode("utf-8").strip()
                                field_name = source_code[decl_node.start_byte:decl_node.end_byte].decode("utf-8").strip()
                                field_decls[field_name] = field_type

            struct_table[struct_name] = field_decls

        # Recurse on children
        for child in n.children:
            walk(child)

    walk(node)

    return struct_table
    