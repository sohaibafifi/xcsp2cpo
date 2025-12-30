"""Connection constraint converters (element, minimum, maximum, channel)."""

from ..model import ElementConstraint, MinMaxConstraint, ChannelConstraint


def convert_element(constraint: ElementConstraint) -> str:
    """Convert element constraint to CPO format."""
    return constraint.to_cpo()


def convert_minimum(constraint: MinMaxConstraint) -> str:
    """Convert minimum constraint to CPO format."""
    return constraint.to_cpo()


def convert_maximum(constraint: MinMaxConstraint) -> str:
    """Convert maximum constraint to CPO format."""
    return constraint.to_cpo()


def convert_channel(constraint: ChannelConstraint) -> str:
    """Convert channel constraint to CPO format."""
    return constraint.to_cpo()
