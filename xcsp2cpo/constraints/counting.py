"""Counting constraint converters (sum, count, nValues, cardinality)."""

from ..model import SumConstraint, CountConstraint, NValuesConstraint, CardinalityConstraint


def convert_sum(constraint: SumConstraint) -> str:
    """Convert sum constraint to CPO format."""
    return constraint.to_cpo()


def convert_count(constraint: CountConstraint) -> str:
    """Convert count constraint to CPO format."""
    return constraint.to_cpo()


def convert_nvalues(constraint: NValuesConstraint) -> str:
    """Convert nValues constraint to CPO format."""
    return constraint.to_cpo()


def convert_cardinality(constraint: CardinalityConstraint) -> str:
    """Convert cardinality constraint to CPO format."""
    return constraint.to_cpo()
