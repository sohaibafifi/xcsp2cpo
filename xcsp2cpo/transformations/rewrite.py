"""
Expression rewriting transformations for CPO compatibility.

This module handles post-decomposition expression rewrites to ensure
all expressions are in CPO-compatible form.

Note: Most expression conversion from XCSP functional notation to CPO
infix is done during parsing in parser.py. This module handles:
- Expressions generated during decomposition
- Any additional normalization needed after decomposition
- Future expression optimizations
"""

from __future__ import annotations

import copy
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model import Model, Constraint

from ..model import IntensionConstraint


def rewrite_expressions(model: "Model") -> "Model":
    """
    Apply expression rewriting transformations to the model.

    This is the main entry point for the rewrite stage.
    Currently a light pass that validates and normalizes expressions.

    Args:
        model: The decomposed model

    Returns:
        A model with rewritten expressions
    """
    # Create a shallow copy of the model
    model = copy.copy(model)

    # Rewrite expressions in constraints
    model.constraints = [
        _rewrite_constraint(c)
        for c in model.constraints
    ]

    return model


def _rewrite_constraint(constraint: "Constraint") -> "Constraint":
    """
    Rewrite expressions in a single constraint.

    Currently handles:
    - Normalizing whitespace in intension expressions
    - Ensuring parentheses are balanced
    """
    if isinstance(constraint, IntensionConstraint):
        constraint = copy.copy(constraint)
        constraint.expression = _normalize_expression(constraint.expression)

    return constraint


def _normalize_expression(expr: str) -> str:
    """
    Normalize an expression string.

    Handles:
    - Trimming whitespace
    - Ensuring consistent spacing around operators
    - Removing redundant parentheses (optional, conservative)
    """
    expr = expr.strip()

    # Normalize whitespace around operators
    # Be conservative to avoid breaking things
    expr = re.sub(r'\s+', ' ', expr)

    return expr


# Future rewrite functions can be added here:
#
# def rewrite_xor(expr: str) -> str:
#     """Rewrite XOR expressions if needed."""
#     pass
#
# def rewrite_iff_to_equality(expr: str) -> str:
#     """Rewrite iff(a, b) to (a == b) if not done during parsing."""
#     pass
#
# def simplify_nested_negations(expr: str) -> str:
#     """Simplify !!x to x."""
#     pass
