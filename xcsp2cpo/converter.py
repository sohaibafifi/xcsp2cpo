"""High-level conversion interface.

This module provides the main API for converting XCSP3 to CPO format.
It uses a transformation pipeline inspired by CPMpy:

    [XCSP3 XML]
        ↓
    parser.py → IR Model
        ↓
    transformations/
      ├── normalize.py    (flatten groups, expand arrays)
      ├── decompose.py    (convert unsupported constraints)
      └── rewrite.py      (normalize expressions)
        ↓
    writer.py → CPO Output
"""

from __future__ import annotations

from .model import Model
from .parser import parse_xcsp, parse_xcsp_file
from .transformations import transform
from .writer import write_cpo_string, write_cpo_file


def convert_to_cpo(xcsp_content: str, use_transformations: bool = True) -> str:
    """Convert XCSP3 XML content to CPO format string.

    Args:
        xcsp_content: XCSP3 XML content as a string
        use_transformations: Whether to use the transformation pipeline (default True)

    Returns:
        CPO format string
    """
    model = parse_xcsp(xcsp_content)

    if use_transformations:
        model = transform(model)

    return write_cpo_string(model)


def convert_file(input_path: str, output_path: str | None = None,
                 use_transformations: bool = True) -> str:
    """Convert XCSP3 file to CPO format.

    Args:
        input_path: Path to input XCSP3 XML file.
        output_path: Optional path to output CPO file. If None, returns string.
        use_transformations: Whether to use the transformation pipeline (default True)

    Returns:
        CPO format string.
    """
    model = parse_xcsp_file(input_path)

    if use_transformations:
        model = transform(model)

    cpo_content = write_cpo_string(model)

    if output_path:
        # Write the transformed model
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cpo_content)

    return cpo_content
