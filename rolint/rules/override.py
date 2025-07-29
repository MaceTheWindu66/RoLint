def detect_override_lines(source_code: str) -> set[int]:
    """
    Parses the source and returns a set of line numbers that should be ignored.
    """

    source_code = source_code.decode('utf-8', errors='ignore')


    ignored_lines = set()
    ignored_blocks = set()
    lines = source_code.splitlines()
    for i, line in enumerate(lines):
        if "rolint: ignore" in line:
            ignored_lines.add(i + 1)  # Ignore the next line (i + 1)
        if "rolint: ignore-block" in line:
            ignored_blocks.add(i + 1)

    return ignored_lines, ignored_blocks

def detect_py_overrides(source_code: str) -> tuple[list[int], list[int]]:
    ignored_lines = []
    ignored_blocks = []


    for lineno, line in enumerate(source_code.splitlines(), start=1):
        stripped = line.strip()
        if "rolint: ignore" in stripped:
            ignored_lines.append(lineno + 1)
        elif "rolint: ignore-block" in stripped:
            ignored_blocks.append(lineno + 1)

    return ignored_lines, ignored_blocks
