import json
from pathlib import Path

def report_json(violations: list[dict], ignored_lines: list[dict]=None, ignored_blocks: list[dict]=None, output_path: Path=None):
    """Writes violations to JSON file"""

    # defaults to rolint_results.json in the rolint directory.
    if not output_path:
        output_path = Path("rolint_results.json")
    
    grouped = {}

    # group violations by file and add
    if violations:
        for v in violations:
            file = v["file"]
            grouped.setdefault(file, []).append({
                "line": v["line"],
                "message": f"VIOLATION: {v["message"]}"
            })

    if ignored_lines:
            for flag in ignored_lines:
                file = flag["file"]
                grouped.setdefault(file, []).append({
                    "line": flag["line"],
                    "message": f"FLAG: Ignored or Overridden Line at Line {flag["line"]}"
                })
    
    if ignored_blocks:
            for flag in ignored_blocks:
                file = flag["file"]
                grouped.setdefault(file, []).append({
                    "line": flag["line"],
                    "message": f"FLAG: Ignored or Overridden Code Block at Line {flag["line"]}"
                })
    # Dump output into json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=2)

