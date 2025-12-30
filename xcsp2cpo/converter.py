"""High-level conversion interface."""

from __future__ import annotations

from .model import Model
from .parser import parse_xcsp, parse_xcsp_file
from .writer import write_cpo_string, write_cpo_file


def convert_to_cpo(xcsp_content: str) -> str:
    """Convert XCSP3 XML content to CPO format string."""
    model = parse_xcsp(xcsp_content)
    return write_cpo_string(model)


def convert_file(input_path: str, output_path: str | None = None) -> str:
    """Convert XCSP3 file to CPO format.

    Args:
        input_path: Path to input XCSP3 XML file.
        output_path: Optional path to output CPO file. If None, returns string.

    Returns:
        CPO format string.
    """
    model = parse_xcsp_file(input_path)
    cpo_content = write_cpo_string(model)

    if output_path:
        write_cpo_file(model, output_path)

    return cpo_content
