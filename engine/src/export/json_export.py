from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from domain.models import ParsedOrder
from .utils import sanitize_filename


def export_to_json(
    result: ParsedOrder,
    output_dir: Union[str, Path],
    filename: Optional[str] = None,
) -> str:
    """
    Export parsed order to JSON file.

    Args:
        result: ParsedOrder object
        output_dir: Directory to save file
        filename: Optional filename (auto-generated if not provided)

    Returns:
        Path to saved file (string)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"{result.get_filename()}.json"

    filename = sanitize_filename(filename)
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result.to_json())

    return str(filepath)
