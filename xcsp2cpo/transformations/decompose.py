"""
Decomposition transformations for unsupported constraints.

This module converts constraints not directly supported by CPO into
equivalent combinations of supported constraints.

Inspired by CPMpy's decompose_global transformation, each decomposition
function takes a constraint and returns a list of equivalent constraints.
"""

from __future__ import annotations

import copy
import warnings
from typing import TYPE_CHECKING, FrozenSet

if TYPE_CHECKING:
    from ..model import Model, Constraint

from ..model import (
    ConstraintType,
    IntensionConstraint,
    AllEqualConstraint,
    OrderedConstraint,
    ChannelConstraint,
)

# Track warned constraint types to avoid repeated warnings
_warned_constraints: set[str] = set()


def decompose_unsupported(model: "Model", supported: FrozenSet[str]) -> "Model":
    """
    Decompose all unsupported constraints in the model.

    This is the main entry point for the decompose stage.
    Iteratively decomposes constraints until all are supported.

    Args:
        model: The normalized model
        supported: Set of supported constraint type names (lowercase)

    Returns:
        A model with only supported constraints
    """
    # Create a copy of the model
    model = copy.copy(model)

    # Decompose constraints iteratively
    model.constraints = decompose_in_tree(model.constraints, supported)

    return model


def decompose_in_tree(constraints: list["Constraint"],
                       supported: FrozenSet[str]) -> list["Constraint"]:
    """
    Recursively decompose unsupported constraints.

    Similar to CPMpy's decompose_in_tree, this handles nested expressions
    and ensures all resulting constraints are supported.

    Args:
        constraints: List of constraints to decompose
        supported: Set of supported constraint type names

    Returns:
        List of supported constraints
    """
    result = []

    for constraint in constraints:
        constraint_type = constraint.type.value.lower()

        if constraint_type in supported:
            # Constraint is supported, keep it
            result.append(constraint)
        else:
            # Decompose and recurse
            decomposed = decompose_constraint(constraint)
            # Recursively check the decomposed constraints
            result.extend(decompose_in_tree(decomposed, supported))

    return result


def decompose_constraint(constraint: "Constraint") -> list["Constraint"]:
    """
    Decompose a single unsupported constraint.

    Dispatches to the appropriate decomposition function based on constraint type.

    Args:
        constraint: The constraint to decompose

    Returns:
        List of equivalent constraints
    """
    if constraint.type == ConstraintType.ALLEQUAL:
        return decompose_allequal(constraint)
    elif constraint.type == ConstraintType.ORDERED:
        return decompose_ordered(constraint)
    elif constraint.type == ConstraintType.CHANNEL:
        return decompose_channel(constraint)
    else:
        # No decomposition known, return as-is
        # This will cause an error later if the constraint is truly unsupported
        return [constraint]


def decompose_allequal(constraint: AllEqualConstraint) -> list["Constraint"]:
    """
    Decompose allEqual into pairwise equality constraints.

    allEqual(x, y, z) → [x == y, x == z]

    CPO doesn't have a native allEqual, so we use pairwise comparisons.
    We compare all variables to the first one (O(n) constraints instead of O(n²)).

    Args:
        constraint: The allEqual constraint

    Returns:
        List of intension constraints expressing pairwise equality
    """
    variables = constraint.variables

    if len(variables) < 2:
        return []

    result = []
    first = variables[0]

    for var in variables[1:]:
        result.append(IntensionConstraint(
            id=None,
            expression=f"{first} == {var}"
        ))

    return result


def decompose_ordered(constraint: OrderedConstraint) -> list["Constraint"]:
    """
    Decompose ordered constraint into comparison chain.

    ordered([x, y, z], le) → [x <= y, y <= z]

    Args:
        constraint: The ordered constraint

    Returns:
        List of intension constraints expressing the ordering
    """
    variables = constraint.variables
    operator = constraint.operator

    # Map XCSP operator to CPO operator
    op_map = {
        "le": "<=",
        "lt": "<",
        "ge": ">=",
        "gt": ">",
    }
    op = op_map.get(operator, "<=")

    result = []
    for i in range(len(variables) - 1):
        result.append(IntensionConstraint(
            id=None,
            expression=f"{variables[i]} {op} {variables[i + 1]}"
        ))

    return result


def decompose_channel(constraint: ChannelConstraint) -> list["Constraint"]:
    """
    Decompose channel constraint into pairwise inverse constraints.

    channel(list1, list2) → [list1[i] == j ⟺ list2[j] == i] for all i, j

    The channel constraint enforces that list1 and list2 are inverse
    permutations of each other.

    Args:
        constraint: The channel constraint

    Returns:
        List of intension constraints expressing the channeling
    """
    list1 = constraint.list1
    list2 = constraint.list2

    result = []
    for i, var1 in enumerate(list1):
        for j, var2 in enumerate(list2):
            # (var1 == j) ⟺ (var2 == i)
            # In CPO: (var1 == j) == (var2 == i)
            result.append(IntensionConstraint(
                id=None,
                expression=f"({var1} == {j}) == ({var2} == {i})"
            ))

    return result


# Future decomposition functions can be added here:
#
# def decompose_circuit(constraint) -> list[Constraint]:
#     """Decompose circuit into subtour elimination constraints."""
#     pass
#
# def decompose_mdd(constraint) -> list[Constraint]:
#     """Decompose MDD into table constraints or equivalent."""
#     pass
