##For parsing C and C++ files

from pathlib import Path
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

# Supported languages
SUPPORTED_LANGUAGES = {"c", "cpp"}

# Language mappings
LANGUAGE_MAP = {
    "c": Language(tsc.language()),
    "cpp": Language(tscpp.language())
}

# Cache for performance
parsers = {}
for lang in SUPPORTED_LANGUAGES:
    parser = Parser(LANGUAGE_MAP[lang])
    parsers[lang] = parser

def parse_file(file_path: Path, lang: str):
    """
    Parse a file and return (tree, source_code)
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}")

    source_code = file_path.read_bytes() 
    tree = parsers[lang].parse(source_code)
    return tree, source_code
