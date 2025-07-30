import json
import yaml
from pathlib import Path
from typing import Any, Optional, Union


SUPPORTED_EXTENSIONS = {".json", ".yml", ".yaml"}


class FileTypeNotSupportedError(Exception):
    pass


def _validate_extension(file_path: Path) -> Path:
    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise FileTypeNotSupportedError(f"Unsupported file extension: {ext}")
    return file_path


def read_file(file_path: Union[str, Path]) -> Any:
    """Read data from a JSON or YAML file."""
    file_path = _validate_extension(Path(file_path))
    with open(file_path, mode="r", encoding="utf-8") as f:
        if file_path.suffix in {".yml", ".yaml"}:
            return yaml.safe_load(f)
        return json.load(f)


def write_file(
    data: Optional[dict],
    file_path: Union[str, Path],
    indent: int = 2,
    sort_keys: bool = False,
) -> bool:
    """Write data to a JSON or YAML file."""
    if data is None:
        return False

    file_path = _validate_extension(Path(file_path))
    with open(file_path, mode="w", encoding="utf-8") as f:
        if file_path.suffix in {".yml", ".yaml"}:
            yaml.dump(data, f, sort_keys=False)
        else:
            json.dump(data, f, indent=indent, sort_keys=sort_keys)
    return True


def print_file(
    data: Optional[dict],
    file_type: str = "json",
    indent: int = 2,
    sort_keys: bool = False,
) -> None:
    """Pretty-print data in JSON or YAML format."""
    if data is None:
        return

    file_type = file_type.lower()
    if file_type in {"yml", "yaml"}:
        print(yaml.dump(data, sort_keys=False))
    else:
        print(json.dumps(data, indent=indent, sort_keys=sort_keys))
