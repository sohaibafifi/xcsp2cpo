"""Generic constraint converters (intension, extension)."""

from ..model import IntensionConstraint, ExtensionConstraint


def convert_intension(constraint: IntensionConstraint) -> str:
    """Convert intension constraint to CPO format."""
    return constraint.to_cpo()


def convert_extension(constraint: ExtensionConstraint) -> str:
    """Convert extension constraint to CPO format."""
    return constraint.to_cpo()
