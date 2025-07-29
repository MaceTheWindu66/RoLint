import subprocess
import threading
import pickle

# Missing type hint for variable
my_data = "hello"

# Unsafe function
eval("print('hi')")

# Unsafe module call
pickle.loads(b"bad_data")

# Thread created but never joined
def thread_example():
    t = threading.Thread(target=lambda: print("Running"))
    t.start()

# Function missing annotations
# rolint: ignore
def do_work(x, y):
    return x + y

# Bare assert
assert 2 + 2 == 4

# Another bare assert as a call
def check():
    assert 1 == 1

# Subprocess without termination
def run_proc():
    proc = subprocess.Popen(["ls", "-l"])
    print("Started process")
