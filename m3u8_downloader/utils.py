import json
from os import path


def vprint(*args):
    """Verbose print function. Will be replaced at runtime based on verbose flag."""
    pass


def load_headers(header_file: str | None) -> dict:
    """Load headers from a JSON file or return default headers."""
    if header_file and path.exists(header_file):
        try:
            with open(header_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse header file {header_file}. Using default headers.")
        except Exception as e:
            print(f"Warning: Error reading header file {header_file}: {e}. Using default headers.")
    
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    }
