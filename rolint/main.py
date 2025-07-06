from pathlib import Path
from collections import defaultdict
from rolint.parser import parser as parser_module
from rolint.rules import c_rules


EXTENSION_MAP = {
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".py": "python"
}

def detect_language(path: Path) -> str:
    return EXTENSION_MAP.get(path.suffix.lower(), None)

def collect_files(base_path: Path) -> dict[str, list[Path]]:
    lang_files = defaultdict(list)
    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            lang = detect_language(file_path)
            if lang:
                lang_files[lang].append(file_path)
    return lang_files

def run_linter(path: Path, lang: str = None, output_format: str = "text"):
    if path.is_dir():
        lang_to_files = collect_files(path)
        if not lang_to_files:
            print("⚠️ No source files found.")
            return
        for lang, files in lang_to_files.items():
            print(f"\n🔧 Linting {len(files)} {lang.upper()} file(s):")
            for f in files:
                print(f"  - {f}")
                run_file_lint(f, lang)
    elif path.is_file():
        inferred_lang = lang or detect_language(path)
        if not inferred_lang:
            print(f"⚠️ Could not detect language for {path}")
            return
        print(f"🔍 Linting: {path}")
        print(f"🌐 Language: {inferred_lang}")
        print(f"📤 Output format: {output_format}")
        run_file_lint(path, inferred_lang)
    else:
        print(f"❌ Path does not exist: {path}")


def run_file_lint(file_path: Path, lang: str):
    if lang == "c":
        from rolint.rules import c_rules
        tree, source = parser_module.parse_file(file_path, lang)
        violations = []
        violations += c_rules.check_banned_functions(tree, source)
        for v in violations:
            print(f"🚫 {file_path}:{v['line']}: {v['message']}")
    elif lang in {"cpp", "python"}:
        print(f"ℹ️ Linting for {lang.upper()} not yet implemented.")
    else:
        print(f"⚠️ Unknown language: {lang}")
