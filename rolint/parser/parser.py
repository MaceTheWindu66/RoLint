##For parsing C and C++ files

from pathlib import Path
from tree_sitter_languages import get_parser

# Supported languages
SUPPORTED_LANGUAGES = {"c", "cpp"}

# Cache for performance
parsers = {lang: get_parser(lang) for lang in SUPPORTED_LANGUAGES}

def parse_file(file_path: Path, lang: str):
    """
    Parse a file and return (tree, source_code)
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}")

    source_code = file_path.read_bytes() 
    tree = parsers[lang].parse(source_code)
    return tree, source_code
