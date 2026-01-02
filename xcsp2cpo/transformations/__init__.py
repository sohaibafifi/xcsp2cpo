"""
Transformation pipeline for XCSP3 to CPO conversion.

Inspired by CPMpy's transformation-based architecture, this module applies
a chain of transformations to convert/decompose constraints into CPO-compatible form.

Pipeline:
    [XCSP3 XML]
        ↓
    parser.py → IR Model (model.py)
        ↓
    transformations/
      ├── normalize.py    (flatten groups, expand arrays)
      ├── decompose.py    (convert unsupported constraints)
      └── rewrite.py      (convert expressions to CPO format)
        ↓
    writer.py → CPO Output

Usage:
    from xcsp2cpo.transformations import transform
    model = parse_xcsp(content)
    model = transform(model)
    output = write_cpo_string(model)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model import Model

from .normalize import normalize
from .decompose import decompose_unsupported
from .rewrite import rewrite_expressions

# Constraints directly supported by CPO (no transformation needed)
# These map to direct CPO constructs
CPO_SUPPORTED_CONSTRAINTS = frozenset({
    "intension",       # → direct expression
    "extension",       # → allowedAssignments() / forbiddenAssignments()
    "alldifferent",    # → alldiff()
    "sum",             # → sum() with comparison
    "count",           # → count()
    "nvalues",         # → numberOfDifferentValues()
    "cardinality",     # → distribute()
    "minimum",         # → min()
    "maximum",         # → max()
    "element",         # → element()
    "cumulative",      # → cumulFunction + pulse
    "nooverlap",       # → noOverlap()
    "regular",         # → automaton (future)
    "instantiation",   # → fixed assignments
})

# Constraints that need decomposition into supported equivalents
DECOMPOSABLE_CONSTRAINTS = frozenset({
    "allequal",        # → pairwise ==
    "ordered",         # → comparison chain
    "channel",         # → pairwise inverse constraints
    "circuit",         # → subtour elimination (future)
    "mdd",             # → table or decomposition (future)
})


def transform(model: "Model") -> "Model":
    """
    Apply the full transformation pipeline.

    Transforms are applied in order, each returning a new (possibly modified) Model.
    Transformations are copy-on-write: original model is not modified.

    Pipeline stages:
        1. normalize: Flatten nested structures, expand array references
        2. decompose: Convert unsupported constraints to supported equivalents
        3. rewrite: Convert expressions to CPO-compatible form

    Args:
        model: The parsed XCSP3 model

    Returns:
        A transformed model ready for CPO output
    """
    model = normalize(model)
    model = decompose_unsupported(model, supported=CPO_SUPPORTED_CONSTRAINTS)
    model = rewrite_expressions(model)
    return model


__all__ = [
    "transform",
    "normalize",
    "decompose_unsupported",
    "rewrite_expressions",
    "CPO_SUPPORTED_CONSTRAINTS",
    "DECOMPOSABLE_CONSTRAINTS",
]
