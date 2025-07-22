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
        self.banned_full = {
            "pickles"
        }
        self.thread_objs = {} # Map for threads {'started': bool, 'joined': bool}
        self.subprocesses = {} # Map for subprocesses

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
        #subprocess graceful termination check
        for pname, data in self.subprocesses.items():
            if not (data["waited"] or data["terminated"] or data["communicated"]):
                self.add(self.path, f"Subprocess '{pname}' started with Popen but not safely terminated or awaited.")

    # Rule for static type checking
    def visit_FunctionDef(self, node):
        self.current_function = node

        args = node.args.args
        if args and args[0].arg == "self":
            args = args[1:]

        for arg in args + node.args.kwonlyargs:
            #Searching arguments for type annotations
            if arg.annotation is None:
                self.add(arg, f"Paramater '{arg.arg}' missing type annotation. Please specify type.")
        if node.returns is None:
            # Check to make sure return type is declared
            self.add(node, f"Function is missing return type annotation.")
        self.generic_visit(node)
        self.current_function = None
    
    #Chillen here because AnnAssign means there's a type hint
    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.generic_visit(node)
    
    #Danger here because a regular assign means no type hint
    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.targets[0], ast.Name) and self.current_function is None:
            self.add(node, f"Variable '{node.targets[0].id}' needs a static type hint.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.banned_functions:
                self.add(node, f"Usage of banned function '{node.func.id}'.")
        if isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name):
                tup = (value.id, node.func.attr)
                if tup in self.banned_full:
                    self.add(node, f"Banned call '{value.id}.{node.func.attr}()'.")

        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.attr == "Thread"
            and node.func.value.id == "threading"
        ):
            # get variable it's assigned to
            parent = getattr(node, 'parent', None)
            if isinstance(parent, ast.Assign) and isinstance(parent.targets[0], ast.Name):
                tname = parent.targets[0].id
                self.thread_objs[tname] = {"started": False, "joined": False}

        #Subprocess tracker
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr == "Popen"
        ):
            parent = getattr(node, 'parent', None)
            if isinstance(parent, ast.Assign) and isinstance(parent.targets[0], ast.Name):
                pname = parent.targets[0].id
                self.subprocesses[pname] = {
                    "waited": False, "terminated": False, "communicated": False
                }

        # start()/join()/terminate()/wait()/communicate() tracking
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):

            tname = node.func.value.id

            if tname in self.thread_objs:
                if node.func.attr == "start":
                    self.thread_objs[tname]["started"] = True
                elif node.func.attr == "join":
                    self.thread_objs[tname]["joined"] = True

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            pname = node.func.value.id
            if pname in self.subprocesses:
                if node.func.attr == "wait":
                    self.subprocesses[pname]["waited"] = True
                elif node.func.attr == "terminate":
                    self.subprocesses[pname]["terminated"] = True
                elif node.func.attr == "communicate":
                    self.subprocesses[pname]["communicated"] = True
    
        
    



def run_python_linter(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))


    linter = PyRules(text, path)
    linter.visit(tree) # Visit all nodes (visit function defined in ast.NodeVisitor class)
    linter.finalize() # Finalize the search by ensuring all threads and subprocesses created were properly terminated

    #Run flake8 for PEP8 standards
    result = subprocess.run(
        ["flake8", str(path), "--ignore=E501,E302"],  # example
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 4:
            lnum = int(parts[1])
            msg = ":".join(parts[3:]).strip()
            linter.violations.append({"line": lnum, "message": f"PEP8 Violation: {msg}"})

    return linter.violations



## Python rules to be implemented:
#      - Static type checking (requiring type hints on variables)
#      - Ban unsafe python functions
#      - Enforce safe threading practices (i.e Graceful Termination)
#      - Enforce PEP8 standards
#      - Enforce runtime assertions (with prebuilt template function rather than assert)
#      -

