import json
from pathlib import Path

CONFIG_FILE = Path.home() / ".rolint_config.json"

# Set up default configuration for users
DEFAULT_CONFIG = {
    "output_path": "rolint_results.json"
}

# load config file
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Config file may be corrupted. Loading default configuration settings.")
            # If config file is corrupted, return default
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy() 


# save new configuration to config file
def save_config(config: dict) -> dict:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)