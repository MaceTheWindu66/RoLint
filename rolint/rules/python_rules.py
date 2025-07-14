import ast
import subprocess
from pathlib import Path
from collections import defaultdict

# Got to make this part of the linter a lot cleaner due to the AST support in python

class PyRules(ast.NodeVisitor):
    def __init__(self, source: str, path: Path):
        self.src = source
        self.path = path
        self.violations = []
        self.current_function = None # Context for current function
        self.banned_functions = {
            "eval", "exec", "compile"
        }
        self.thread_objs = {} # Map for threads {'started': bool, 'joined': bool}

    def add(self, node, msg):
        """
        Helper function to add violations to the list
        """
        self.violations.append({
            "line": node.lineno,
            "message": msg
        })

    def finalize(self):
        # Check to ensure all threading.Threads have been joined
        for tname, data in self.thread_objs.items():
            if data["started"] and not data["joined"]:
                self.add(self.path, f"Thead '{tname}' started but never joined.")
    



def run_python_linter(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))


    linter = PyRules(text, path)
    linter.visit(tree) # Visit all nodes (visit function defined in ast.NodeVisitor class)
    linter.finalize()

    return linter.violations



## Python rules to be implemented:
#      - Static type checking (requiring type hints on variables)
#      - Ban unsafe python functions
#      - Enforce safe threading practices (i.e Graceful Termination)
#      - Enforce PEP8 standards
#      - Enforce runtime assertions (with prebuilt template function rather than assert)
#      -

