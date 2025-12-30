"""CPO file writer."""

from typing import TextIO
import sys

from .model import Model


def write_cpo(model: Model, output: TextIO = sys.stdout) -> None:
    """Write model to CPO format."""
    output.write(model.to_cpo())
    output.write("\n")


def write_cpo_file(model: Model, filepath: str) -> None:
    """Write model to CPO file."""
    with open(filepath, "w", encoding="utf-8") as f:
        write_cpo(model, f)


def write_cpo_string(model: Model) -> str:
    """Convert model to CPO string."""
    return model.to_cpo()
