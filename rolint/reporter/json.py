import json
from pathlib import Path

def report_json(violations: list[dict], output_path: Path=None):
    """Writes violations to JSON file"""

    # defaults to rolint_results.json in the rolint directory.
    if not output_path:
        output_path = Path("rolint_results.json")
    
    grouped = {}

    # group violations by file and add
    for v in violations:
        file = v["file"]
        grouped.setdefault(file, []).append({
            "line": v["line"],
            "message": v["message"]
        })

    # Dump output into json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=2)

