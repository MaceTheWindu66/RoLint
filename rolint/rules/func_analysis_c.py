from collections import defaultdict

## Helper file for detecting recursion and mutual recursion in C functions. Recursion is banned through this linter.

def collect_function_definitions(root_node, source_code: bytes) -> dict:
    """
    Walks the AST to collect all function_definition nodes.
    Returns: dict mapping function names to their function_definition node.
    """
    functions = {}

    def walk(node):
        if node.type == "function_definition":
            declarator = node.child_by_field_name("declarator")
            if declarator is not None:
                # Handle nested pointers, declarator chains
                ident_node = declarator
                while ident_node.type != "identifier" and ident_node.child_by_field_name("declarator"):
                    ident_node = ident_node.child_by_field_name("declarator")

                if ident_node.type == "identifier":
                    func_name = source_code[ident_node.start_byte:ident_node.end_byte].decode("utf-8")
                    functions[func_name] = node

        for child in node.children:
            walk(child)

    walk(root_node)
    return functions


def build_call_graph(functions, source_code):
    graph = defaultdict(list)

    for name, body in functions.items():
        if not body:
            continue

        def walk(node):
            if node.type == "call_expression":
                callee_node = node.child_by_field_name("function")
                if callee_node and callee_node.type == "identifier":
                    callee = source_code[callee_node.start_byte:callee_node.end_byte].decode("utf-8")
                    graph[name].append(callee)
            for child in node.children:
                walk(child)

        walk(body)

    return graph

def detect_recursive_functions(call_graph):
    visited = set()
    stack = set()
    recursive = set()

    def dfs(func):
        if func in stack:
            recursive.add(func)
            return
        if func in visited:
            return
        visited.add(func)
        stack.add(func)
        for callee in call_graph.get(func, []):
            dfs(callee)
        stack.remove(func)

    for func in call_graph:
        dfs(func)

    return recursive
