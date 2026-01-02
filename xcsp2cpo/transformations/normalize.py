"""
Normalization transformations for XCSP3 models.

This module handles:
- Flattening nested constraint groups/blocks
- Normalizing variable references
- Expanding array references (e.g., y[] → y[0], y[1], ...)
"""

from __future__ import annotations

import copy
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model import Model, Constraint


def normalize(model: "Model") -> "Model":
    """
    Apply all normalization transformations to the model.

    This is the main entry point for the normalize stage.
    Creates a copy of the model to avoid modifying the original.

    Args:
        model: The parsed XCSP3 model

    Returns:
        A normalized copy of the model
    """
    # Create a shallow copy of the model
    model = copy.copy(model)

    # Build variable lookup for array expansion
    var_lookup = _build_variable_lookup(model)

    # Normalize constraints
    model.constraints = [
        _normalize_constraint(c, var_lookup)
        for c in model.constraints
    ]

    return model


def _build_variable_lookup(model: "Model") -> dict:
    """
    Build a lookup dictionary for variable/array information.

    Returns a dict mapping:
        - var_id → {'type': 'var'}
        - array_id → {'type': 'array', 'size': [dims], 'start_index': int}
    """
    lookup = {}

    for var in model.variables:
        lookup[var.id] = {'type': 'var'}

    for arr in model.arrays:
        lookup[arr.id] = {
            'type': 'array',
            'size': arr.size,
            'start_index': arr.start_index
        }

    return lookup


def _normalize_constraint(constraint: "Constraint", var_lookup: dict) -> "Constraint":
    """
    Normalize a single constraint.

    - Expands array references in variable lists
    - Normalizes variable names
    """
    # Create a copy to avoid modifying original
    constraint = copy.copy(constraint)

    # Expand array references in variable lists
    if hasattr(constraint, 'variables') and constraint.variables:
        constraint.variables = _expand_variable_list(constraint.variables, var_lookup)

    if hasattr(constraint, 'list1') and constraint.list1:
        constraint.list1 = _expand_variable_list(constraint.list1, var_lookup)

    if hasattr(constraint, 'list2') and constraint.list2:
        constraint.list2 = _expand_variable_list(constraint.list2, var_lookup)

    return constraint


def _expand_variable_list(var_list: list[str], var_lookup: dict) -> list[str]:
    """
    Expand array references in a variable list.

    Examples:
        ['x', 'y[]'] → ['x', 'y[0]', 'y[1]', 'y[2]', ...]
        ['x', 'y[0]', 'y[1]'] → ['x', 'y[0]', 'y[1]']  (unchanged)
    """
    expanded = []

    for var_ref in var_list:
        expanded_refs = _expand_single_reference(var_ref, var_lookup)
        expanded.extend(expanded_refs)

    return expanded


def _expand_single_reference(var_ref: str, var_lookup: dict) -> list[str]:
    """
    Expand a single variable reference.

    Handles:
        - Plain variables: 'x' → ['x']
        - Indexed arrays: 'y[0]' → ['y[0]']
        - Full array expansion: 'y[]' → ['y[0]', 'y[1]', ...]
        - Range expansion: 'y[0..2]' → ['y[0]', 'y[1]', 'y[2]']
    """
    var_ref = var_ref.strip()

    # Check for array expansion pattern: arr[]
    match = re.match(r'^(\w+)\[\s*\]$', var_ref)
    if match:
        arr_name = match.group(1)
        if arr_name in var_lookup and var_lookup[arr_name]['type'] == 'array':
            arr_info = var_lookup[arr_name]
            size = arr_info['size']
            start = arr_info['start_index']
            # For 1D arrays
            if len(size) == 1:
                return [f"{arr_name}[{i}]" for i in range(start, start + size[0])]
            else:
                # For multi-dimensional, flatten
                total = 1
                for dim in size:
                    total *= dim
                return [f"{arr_name}[{i}]" for i in range(start, start + total)]
        # If not found in lookup, return as-is
        return [var_ref]

    # Check for range expansion: arr[0..2]
    match = re.match(r'^(\w+)\[\s*(\d+)\s*\.\.\s*(\d+)\s*\]$', var_ref)
    if match:
        arr_name = match.group(1)
        start = int(match.group(2))
        end = int(match.group(3))
        return [f"{arr_name}[{i}]" for i in range(start, end + 1)]

    # Check for comma-separated indices: arr[0,1,2]
    match = re.match(r'^(\w+)\[\s*(.+)\s*\]$', var_ref)
    if match:
        arr_name = match.group(1)
        indices_str = match.group(2)
        # Check if it's comma-separated list
        if ',' in indices_str and '..' not in indices_str:
            indices = [idx.strip() for idx in indices_str.split(',')]
            return [f"{arr_name}[{idx}]" for idx in indices]

    # Default: return as-is (plain variable or already indexed)
    return [var_ref]


def expand_array_reference(var_ref: str, array_sizes: dict[str, list[int]],
                           start_indices: dict[str, int] | None = None) -> list[str]:
    """
    Public helper to expand array references.

    Args:
        var_ref: The variable reference string
        array_sizes: Dict mapping array names to their sizes
        start_indices: Optional dict mapping array names to start indices (default 0)

    Returns:
        List of expanded variable references
    """
    if start_indices is None:
        start_indices = {}

    var_lookup = {
        name: {
            'type': 'array',
            'size': size,
            'start_index': start_indices.get(name, 0)
        }
        for name, size in array_sizes.items()
    }

    return _expand_single_reference(var_ref, var_lookup)
