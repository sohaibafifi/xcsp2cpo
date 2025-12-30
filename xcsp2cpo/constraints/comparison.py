"""Comparison constraint converters (allDifferent, allEqual, ordered)."""

from ..model import AllDifferentConstraint, AllEqualConstraint, OrderedConstraint


def convert_alldifferent(constraint: AllDifferentConstraint) -> str:
    """Convert allDifferent constraint to CPO format."""
    return constraint.to_cpo()


def convert_allequal(constraint: AllEqualConstraint) -> str:
    """Convert allEqual constraint to CPO format."""
    return constraint.to_cpo()


def convert_ordered(constraint: OrderedConstraint) -> str:
    """Convert ordered constraint to CPO format."""
    return constraint.to_cpo()
