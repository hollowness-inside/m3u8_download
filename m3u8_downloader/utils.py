import json
from os import path


class Config:
    _verbose = False

    @classmethod
    def set_verbose(cls, verbose: bool):
        cls._verbose = verbose

    @classmethod
    def is_verbose(cls) -> bool:
        return cls._verbose


def vprint(*args):
    """Verbose print function that uses the Config class to determine verbosity."""
    if Config.is_verbose():
        print(*args)


def load_headers(header_file: str | None) -> dict:
    """Load headers from a JSON file or return default headers."""
    if header_file and path.exists(header_file):
        try:
            with open(header_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(
                f"Warning: Failed to parse header file {header_file}. Using default headers."
            )
        except Exception as e:
            print(
                f"Warning: Error reading header file {header_file}: {e}. Using default headers."
            )

    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    }
