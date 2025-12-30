"""Internal representation (IR) for XCSP3 models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


class ProblemType(Enum):
    """Type of constraint problem."""
    CSP = "CSP"
    COP = "COP"


class ConstraintType(Enum):
    """Types of constraints supported."""
    INTENSION = "intension"
    EXTENSION = "extension"
    ALLDIFFERENT = "allDifferent"
    ALLEQUAL = "allEqual"
    ORDERED = "ordered"
    SUM = "sum"
    COUNT = "count"
    NVALUES = "nValues"
    CARDINALITY = "cardinality"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    ELEMENT = "element"
    CHANNEL = "channel"
    CUMULATIVE = "cumulative"
    NOOVERLAP = "noOverlap"
    REGULAR = "regular"
    MDD = "mdd"
    CIRCUIT = "circuit"
    INSTANTIATION = "instantiation"


class ObjectiveType(Enum):
    """Types of objectives."""
    EXPRESSION = "expression"
    SUM = "sum"
    PRODUCT = "product"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    NVALUES = "nValues"
    LEX = "lex"


class ConditionOperator(Enum):
    """Comparison operators for conditions."""
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    EQ = "eq"
    NE = "ne"
    IN = "in"
    NOTIN = "notin"


@dataclass
class Domain:
    """Represents a variable domain."""
    values: list[int] = field(default_factory=list)
    ranges: list[tuple[int, int]] = field(default_factory=list)

    def to_cpo(self) -> str:
        """Convert domain to CPO format."""
        parts = []
        for start, end in self.ranges:
            if start == end:
                parts.append(str(start))
            else:
                parts.append(f"{start}..{end}")
        for val in self.values:
            if not any(start <= val <= end for start, end in self.ranges):
                parts.append(str(val))
        return ", ".join(parts) if parts else "0..0"

    @classmethod
    def from_string(cls, s: str) -> "Domain":
        """Parse domain from XCSP string format."""
        domain = cls()
        s = s.strip()
        if not s:
            return domain

        parts = s.replace(",", " ").split()
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if ".." in part:
                start, end = part.split("..")
                domain.ranges.append((int(start), int(end)))
            else:
                domain.values.append(int(part))
        return domain


@dataclass
class Variable:
    """Represents a single variable."""
    id: str
    domain: Domain

    def to_cpo(self) -> str:
        """Convert variable to CPO declaration."""
        return f"{self.id} = intVar({self.domain.to_cpo()});"


@dataclass
class Array:
    """Represents an array of variables."""
    id: str
    size: list[int]  # dimensions, e.g. [5] for 1D, [3, 4] for 2D
    domain: Domain
    start_index: int = 0

    def to_cpo(self) -> str:
        """Convert array to CPO declarations."""
        if len(self.size) == 1:
            # 1D array
            vars_str = ", ".join(
                f"intVar({self.domain.to_cpo()})"
                for _ in range(self.size[0])
            )
            return f"{self.id} = [{vars_str}];"
        else:
            # Multi-dimensional array - flatten or create nested
            lines = []
            total = 1
            for dim in self.size:
                total *= dim
            vars_str = ", ".join(
                f"intVar({self.domain.to_cpo()})"
                for _ in range(total)
            )
            lines.append(f"{self.id} = [{vars_str}];")
            return "\n".join(lines)

    def get_total_size(self) -> int:
        """Get total number of variables in array."""
        total = 1
        for dim in self.size:
            total *= dim
        return total


@dataclass
class Condition:
    """Represents a condition like (le, 100) or (in, 1..10)."""
    operator: ConditionOperator
    operand: Union[int, str, tuple[int, int], list[int]]  # value, var, range, or set

    def to_cpo_operator(self) -> str:
        """Convert operator to CPO format."""
        op_map = {
            ConditionOperator.LT: "<",
            ConditionOperator.LE: "<=",
            ConditionOperator.GT: ">",
            ConditionOperator.GE: ">=",
            ConditionOperator.EQ: "==",
            ConditionOperator.NE: "!=",
        }
        return op_map.get(self.operator, "==")


@dataclass
class Constraint:
    """Base class for all constraints."""
    id: Optional[str] = None
    type: ConstraintType = ConstraintType.INTENSION

    def to_cpo(self) -> str:
        """Convert constraint to CPO format."""
        raise NotImplementedError


@dataclass
class IntensionConstraint(Constraint):
    """Intension constraint with functional expression."""
    type: ConstraintType = field(default=ConstraintType.INTENSION, init=False)
    expression: str = ""

    def to_cpo(self) -> str:
        return f"{self.expression};"


@dataclass
class ExtensionConstraint(Constraint):
    """Extension (table) constraint."""
    type: ConstraintType = field(default=ConstraintType.EXTENSION, init=False)
    variables: list[str] = field(default_factory=list)
    tuples: list[tuple] = field(default_factory=list)
    is_support: bool = True  # True for supports, False for conflicts

    def to_cpo(self) -> str:
        func = "allowedAssignments" if self.is_support else "forbiddenAssignments"
        vars_str = ", ".join(self.variables)
        tuples_str = ", ".join(
            f"({', '.join(str(v) for v in t)})" for t in self.tuples
        )
        return f"{func}([{vars_str}], [{tuples_str}]);"


@dataclass
class AllDifferentConstraint(Constraint):
    """AllDifferent constraint."""
    type: ConstraintType = field(default=ConstraintType.ALLDIFFERENT, init=False)
    variables: list[str] = field(default_factory=list)
    except_values: list[int] = field(default_factory=list)

    def to_cpo(self) -> str:
        vars_str = ", ".join(self.variables)
        return f"alldiff([{vars_str}]);"


@dataclass
class AllEqualConstraint(Constraint):
    """AllEqual constraint."""
    type: ConstraintType = field(default=ConstraintType.ALLEQUAL, init=False)
    variables: list[str] = field(default_factory=list)

    def to_cpo(self) -> str:
        # CPO doesn't have allEqual, use pairwise equality
        if len(self.variables) < 2:
            return ""
        constraints = []
        first = self.variables[0]
        for var in self.variables[1:]:
            constraints.append(f"{first} == {var};")
        return "\n".join(constraints)


@dataclass
class OrderedConstraint(Constraint):
    """Ordered constraint (lex ordering)."""
    type: ConstraintType = field(default=ConstraintType.ORDERED, init=False)
    variables: list[str] = field(default_factory=list)
    operator: str = "le"  # le, lt, ge, gt

    def to_cpo(self) -> str:
        op_map = {"le": "<=", "lt": "<", "ge": ">=", "gt": ">"}
        op = op_map.get(self.operator, "<=")
        constraints = []
        for i in range(len(self.variables) - 1):
            constraints.append(f"{self.variables[i]} {op} {self.variables[i+1]};")
        return "\n".join(constraints)


@dataclass
class SumConstraint(Constraint):
    """Sum constraint."""
    type: ConstraintType = field(default=ConstraintType.SUM, init=False)
    variables: list[str] = field(default_factory=list)
    coefficients: list[int] = field(default_factory=list)
    condition: Optional[Condition] = None

    def to_cpo(self) -> str:
        if self.coefficients and len(self.coefficients) == len(self.variables):
            terms = [
                f"{c}*{v}" if c != 1 else v
                for c, v in zip(self.coefficients, self.variables)
            ]
            sum_expr = " + ".join(terms)
        else:
            vars_str = ", ".join(self.variables)
            sum_expr = f"sum([{vars_str}])"

        if self.condition:
            if self.condition.operator == ConditionOperator.IN:
                # Range constraint
                if isinstance(self.condition.operand, tuple):
                    low, high = self.condition.operand
                    return f"{sum_expr} >= {low};\n{sum_expr} <= {high};"
            op = self.condition.to_cpo_operator()
            return f"{sum_expr} {op} {self.condition.operand};"
        return f"{sum_expr};"


@dataclass
class CountConstraint(Constraint):
    """Count constraint."""
    type: ConstraintType = field(default=ConstraintType.COUNT, init=False)
    variables: list[str] = field(default_factory=list)
    value: Union[int, str] = 0
    condition: Optional[Condition] = None

    def to_cpo(self) -> str:
        vars_str = ", ".join(self.variables)
        count_expr = f"count([{vars_str}], {self.value})"
        if self.condition:
            op = self.condition.to_cpo_operator()
            return f"{count_expr} {op} {self.condition.operand};"
        return f"{count_expr};"


@dataclass
class NValuesConstraint(Constraint):
    """NValues constraint (number of distinct values)."""
    type: ConstraintType = field(default=ConstraintType.NVALUES, init=False)
    variables: list[str] = field(default_factory=list)
    condition: Optional[Condition] = None

    def to_cpo(self) -> str:
        vars_str = ", ".join(self.variables)
        nvalues_expr = f"numberOfDifferentValues([{vars_str}])"
        if self.condition:
            op = self.condition.to_cpo_operator()
            return f"{nvalues_expr} {op} {self.condition.operand};"
        return f"{nvalues_expr};"


@dataclass
class CardinalityConstraint(Constraint):
    """Cardinality (global cardinality) constraint."""
    type: ConstraintType = field(default=ConstraintType.CARDINALITY, init=False)
    variables: list[str] = field(default_factory=list)
    values: list[int] = field(default_factory=list)
    occurrences: list[Union[int, str, tuple]] = field(default_factory=list)

    def to_cpo(self) -> str:
        vars_str = ", ".join(self.variables)
        values_str = ", ".join(str(v) for v in self.values)
        # CPO distribute function
        occ_vars = ", ".join(
            str(o) if isinstance(o, int) else o
            for o in self.occurrences
        )
        return f"distribute([{occ_vars}], [{values_str}], [{vars_str}]);"


@dataclass
class ElementConstraint(Constraint):
    """Element constraint."""
    type: ConstraintType = field(default=ConstraintType.ELEMENT, init=False)
    array: str = ""
    index: str = ""
    value: Union[int, str] = 0

    def to_cpo(self) -> str:
        return f"element({self.array}, {self.index}) == {self.value};"


@dataclass
class MinMaxConstraint(Constraint):
    """Minimum or Maximum constraint."""
    type: ConstraintType = ConstraintType.MINIMUM
    variables: list[str] = field(default_factory=list)
    condition: Optional[Condition] = None

    def to_cpo(self) -> str:
        func = "min" if self.type == ConstraintType.MINIMUM else "max"
        vars_str = ", ".join(self.variables)
        expr = f"{func}([{vars_str}])"
        if self.condition:
            op = self.condition.to_cpo_operator()
            return f"{expr} {op} {self.condition.operand};"
        return f"{expr};"


@dataclass
class ChannelConstraint(Constraint):
    """Channel constraint."""
    type: ConstraintType = field(default=ConstraintType.CHANNEL, init=False)
    list1: list[str] = field(default_factory=list)
    list2: list[str] = field(default_factory=list)

    def to_cpo(self) -> str:
        # Channel: list1[i] = j <=> list2[j] = i
        constraints = []
        for i, var1 in enumerate(self.list1):
            for j, var2 in enumerate(self.list2):
                constraints.append(f"({var1} == {j}) == ({var2} == {i});")
        return "\n".join(constraints)


@dataclass
class Objective:
    """Represents an optimization objective."""
    type: ObjectiveType = ObjectiveType.EXPRESSION
    minimize: bool = True
    expression: str = ""
    variables: list[str] = field(default_factory=list)
    coefficients: list[int] = field(default_factory=list)

    def to_cpo(self) -> str:
        func = "minimize" if self.minimize else "maximize"

        if self.type == ObjectiveType.EXPRESSION:
            return f"{func}({self.expression});"
        elif self.type == ObjectiveType.SUM:
            if self.coefficients and len(self.coefficients) == len(self.variables):
                terms = [
                    f"{c}*{v}" if c != 1 else v
                    for c, v in zip(self.coefficients, self.variables)
                ]
                expr = " + ".join(terms)
            else:
                vars_str = ", ".join(self.variables)
                expr = f"sum([{vars_str}])"
            return f"{func}({expr});"
        elif self.type in (ObjectiveType.MINIMUM, ObjectiveType.MAXIMUM):
            agg_func = "min" if self.type == ObjectiveType.MINIMUM else "max"
            vars_str = ", ".join(self.variables)
            return f"{func}({agg_func}([{vars_str}]));"
        elif self.type == ObjectiveType.PRODUCT:
            vars_str = " * ".join(self.variables)
            return f"{func}({vars_str});"
        else:
            vars_str = ", ".join(self.variables)
            return f"{func}(sum([{vars_str}]));"


@dataclass
class Model:
    """Complete XCSP3 model representation."""
    problem_type: ProblemType = ProblemType.CSP
    variables: list[Variable] = field(default_factory=list)
    arrays: list[Array] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    objectives: list[Objective] = field(default_factory=list)

    def to_cpo(self) -> str:
        """Convert entire model to CPO format."""
        lines = []

        # Variables section
        lines.append("// Variables")
        for var in self.variables:
            lines.append(var.to_cpo())
        for arr in self.arrays:
            lines.append(arr.to_cpo())

        lines.append("")
        lines.append("// Constraints")
        for constraint in self.constraints:
            cpo = constraint.to_cpo()
            if cpo:
                lines.append(cpo)

        if self.objectives:
            lines.append("")
            lines.append("// Objective")
            for obj in self.objectives:
                lines.append(obj.to_cpo())

        return "\n".join(lines)
