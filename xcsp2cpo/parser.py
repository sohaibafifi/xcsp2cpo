"""XCSP3 XML parser."""

from __future__ import annotations

import lzma
import re
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

from .model import (
    Model, ProblemType, Variable, Array, Domain, Constraint, Objective,
    ConstraintType, ObjectiveType, ConditionOperator, Condition,
    IntensionConstraint, ExtensionConstraint, AllDifferentConstraint,
    AllEqualConstraint, OrderedConstraint, SumConstraint, CountConstraint,
    NValuesConstraint, CardinalityConstraint, ElementConstraint,
    MinMaxConstraint, ChannelConstraint,
)


def parse_xcsp(xml_content: str) -> Model:
    """Parse XCSP3 XML content into a Model."""
    root = ET.fromstring(xml_content)
    model = Model()

    # Parse problem type
    problem_type = root.get("type", "CSP")
    model.problem_type = ProblemType.COP if problem_type == "COP" else ProblemType.CSP

    # Parse variables
    variables_elem = root.find("variables")
    if variables_elem is not None:
        _parse_variables(variables_elem, model)

    # Parse constraints
    constraints_elem = root.find("constraints")
    if constraints_elem is not None:
        _parse_constraints(constraints_elem, model)

    # Parse objectives
    objectives_elem = root.find("objectives")
    if objectives_elem is not None:
        _parse_objectives(objectives_elem, model)

    return model


def parse_xcsp_file(filepath: str | Path) -> Model:
    """Parse XCSP3 XML file into a Model.

    Supports both plain XML files and LZMA-compressed XML files (.xml.lzma).

    Args:
        filepath: Path to the XCSP3 file (can be .xml or .xml.lzma)

    Returns:
        Parsed Model
    """
    filepath = Path(filepath)

    if filepath.suffix == ".lzma" or str(filepath).endswith(".xml.lzma"):
        # LZMA-compressed file
        with lzma.open(filepath, "rt", encoding="utf-8") as f:
            return parse_xcsp(f.read())
    else:
        # Plain XML file
        with open(filepath, "r", encoding="utf-8") as f:
            return parse_xcsp(f.read())


def _parse_variables(elem: ET.Element, model: Model) -> None:
    """Parse variables section."""
    for child in elem:
        if child.tag == "var":
            var = _parse_var(child)
            if var:
                model.variables.append(var)
        elif child.tag == "array":
            arr = _parse_array(child)
            if arr:
                model.arrays.append(arr)


def _parse_var(elem: ET.Element) -> Optional[Variable]:
    """Parse a single variable declaration."""
    var_id = elem.get("id")
    if not var_id:
        return None

    # Check for symbolic type (string domain) - not supported
    var_type = elem.get("type", "integer")
    if var_type == "symbolic":
        warnings.warn(
            f"Variable '{var_id}' has symbolic (string) domain which is not supported. "
            f"Skipping this variable.",
            UserWarning
        )
        return None

    # Check for "as" attribute (referencing another variable's domain)
    as_ref = elem.get("as")
    if as_ref:
        # This variable references another's domain
        # For now, we can't resolve this without more context
        # Just use a default domain and warn if symbolic
        warnings.warn(
            f"Variable '{var_id}' uses 'as' reference to '{as_ref}'. "
            f"Domain resolution not fully supported.",
            UserWarning
        )
        return None

    domain_str = elem.text.strip() if elem.text else "0..1"
    domain = Domain.from_string(domain_str)

    return Variable(id=var_id, domain=domain)


def _parse_array(elem: ET.Element) -> Optional[Array]:
    """Parse an array declaration."""
    arr_id = elem.get("id")
    if not arr_id:
        return None

    size_str = elem.get("size", "[1]")
    size = _parse_size(size_str)

    start_index = int(elem.get("startIndex", "0"))

    domain_str = elem.text.strip() if elem.text else "0..1"
    domain = Domain.from_string(domain_str)

    return Array(id=arr_id, size=size, domain=domain, start_index=start_index)


def _parse_size(size_str: str) -> list[int]:
    """Parse array size string like '[5]' or '[3][4]'."""
    matches = re.findall(r"\[(\d+)\]", size_str)
    return [int(m) for m in matches] if matches else [1]


def _parse_constraints(elem: ET.Element, model: Model) -> None:
    """Parse constraints section."""
    for child in elem:
        constraint = _parse_constraint(child, model)
        if constraint:
            if isinstance(constraint, list):
                model.constraints.extend(constraint)
            else:
                model.constraints.append(constraint)


def _parse_constraint(elem: ET.Element, model: Model) -> Optional[Constraint | list[Constraint]]:
    """Parse a single constraint element."""
    tag = elem.tag.lower()
    constraint_id = elem.get("id")

    if tag == "intension":
        return _parse_intension(elem, constraint_id, model)
    elif tag == "extension":
        return _parse_extension(elem, constraint_id, model)
    elif tag == "alldifferent":
        return _parse_alldifferent(elem, constraint_id, model)
    elif tag == "allequal":
        return _parse_allequal(elem, constraint_id, model)
    elif tag == "ordered":
        return _parse_ordered(elem, constraint_id, model)
    elif tag == "sum":
        return _parse_sum(elem, constraint_id, model)
    elif tag == "count":
        return _parse_count(elem, constraint_id, model)
    elif tag == "nvalues":
        return _parse_nvalues(elem, constraint_id, model)
    elif tag == "cardinality":
        return _parse_cardinality(elem, constraint_id, model)
    elif tag == "element":
        return _parse_element(elem, constraint_id, model)
    elif tag == "minimum":
        return _parse_minmax(elem, constraint_id, model, is_min=True)
    elif tag == "maximum":
        return _parse_minmax(elem, constraint_id, model, is_min=False)
    elif tag == "channel":
        return _parse_channel(elem, constraint_id, model)
    elif tag == "group":
        return _parse_group(elem, model)
    elif tag == "block":
        return _parse_block(elem, model)
    else:
        # Unknown constraint type - emit warning
        warnings.warn(
            f"Unknown constraint type '{tag}' encountered during parsing. "
            f"This constraint will be skipped.",
            UserWarning
        )
        return None


def _parse_intension(elem: ET.Element, constraint_id: Optional[str], model: Model) -> IntensionConstraint:
    """Parse intension constraint."""
    # Get the function element or direct text
    func_elem = elem.find("function")
    if func_elem is not None and func_elem.text:
        expr = func_elem.text.strip()
    elif elem.text:
        expr = elem.text.strip()
    else:
        expr = ""

    # Convert XCSP functional notation to CPO infix
    cpo_expr = _convert_expression(expr, model)

    return IntensionConstraint(id=constraint_id, expression=cpo_expr)


def _convert_expression(expr: str, model: Model) -> str:
    """Convert XCSP functional expression to CPO infix notation."""
    expr = expr.strip()

    # Handle function calls: func(args)
    match = re.match(r"(\w+)\((.+)\)$", expr, re.DOTALL)
    if match:
        func_name = match.group(1).lower()
        args_str = match.group(2)
        args = _split_args(args_str)
        converted_args = [_convert_expression(arg, model) for arg in args]

        # Binary operators
        binary_ops = {
            "add": "+", "sub": "-", "mul": "*", "div": "/",
            "mod": "%", "pow": "^",
            "lt": "<", "le": "<=", "gt": ">", "ge": ">=",
            "eq": "==", "ne": "!=",
            "and": "&&", "or": "||", "imp": "=>", "iff": "==",
        }
        if func_name in binary_ops and len(converted_args) == 2:
            op = binary_ops[func_name]
            return f"({converted_args[0]} {op} {converted_args[1]})"

        # N-ary operators
        if func_name == "add" and len(converted_args) > 2:
            return "(" + " + ".join(converted_args) + ")"
        if func_name == "mul" and len(converted_args) > 2:
            return "(" + " * ".join(converted_args) + ")"
        if func_name == "and" and len(converted_args) > 2:
            return "(" + " && ".join(converted_args) + ")"
        if func_name == "or" and len(converted_args) > 2:
            return "(" + " || ".join(converted_args) + ")"

        # Unary operators
        if func_name == "neg" and len(converted_args) == 1:
            return f"(-{converted_args[0]})"
        if func_name == "not" and len(converted_args) == 1:
            return f"(!{converted_args[0]})"
        if func_name == "abs" and len(converted_args) == 1:
            return f"abs({converted_args[0]})"

        # Min/max
        if func_name == "min":
            return f"min([{', '.join(converted_args)}])"
        if func_name == "max":
            return f"max([{', '.join(converted_args)}])"

        # If-then-else
        if func_name == "if" and len(converted_args) == 3:
            return f"({converted_args[0]} ? {converted_args[1]} : {converted_args[2]})"

        # Dist (absolute difference)
        if func_name == "dist" and len(converted_args) == 2:
            return f"abs({converted_args[0]} - {converted_args[1]})"

        # Default: keep as function call
        return f"{func_name}({', '.join(converted_args)})"

    # Variable reference with array index: x[i] or x[0]
    if re.match(r"\w+\[\d+\]", expr):
        return expr

    # Plain variable or number
    return expr


def _split_args(args_str: str) -> list[str]:
    """Split function arguments handling nested parentheses."""
    args = []
    current = ""
    depth = 0

    for char in args_str:
        if char == "(":
            depth += 1
            current += char
        elif char == ")":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        args.append(current.strip())

    return args


def _parse_extension(elem: ET.Element, constraint_id: Optional[str], model: Model) -> ExtensionConstraint:
    """Parse extension (table) constraint."""
    # Parse variable list
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    else:
        variables = []

    # Parse supports or conflicts
    supports_elem = elem.find("supports")
    conflicts_elem = elem.find("conflicts")

    is_support = supports_elem is not None
    tuples_elem = supports_elem if is_support else conflicts_elem

    tuples = []
    if tuples_elem is not None and tuples_elem.text:
        tuples = _parse_tuples(tuples_elem.text.strip())

    return ExtensionConstraint(
        id=constraint_id,
        variables=variables,
        tuples=tuples,
        is_support=is_support
    )


def _parse_tuples(tuples_str: str) -> list[tuple]:
    """Parse tuple list like '(0,1,0)(1,0,0)(1,1,1)'."""
    tuples = []
    # Match tuples in parentheses
    matches = re.findall(r"\(([^)]+)\)", tuples_str)
    for match in matches:
        values = [int(v.strip()) for v in match.split(",") if v.strip() != "*"]
        tuples.append(tuple(values))

    # Handle space-separated values for unary constraints
    if not tuples:
        parts = tuples_str.split()
        for part in parts:
            if ".." in part:
                start, end = part.split("..")
                for v in range(int(start), int(end) + 1):
                    tuples.append((v,))
            else:
                try:
                    tuples.append((int(part),))
                except ValueError:
                    pass

    return tuples


def _parse_alldifferent(elem: ET.Element, constraint_id: Optional[str], model: Model) -> AllDifferentConstraint:
    """Parse allDifferent constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    elif elem.text:
        variables = _parse_variable_list(elem.text.strip(), model)
    else:
        variables = []

    except_elem = elem.find("except")
    except_values = []
    if except_elem is not None and except_elem.text:
        except_values = [int(v.strip()) for v in except_elem.text.strip().split()]

    return AllDifferentConstraint(
        id=constraint_id,
        variables=variables,
        except_values=except_values
    )


def _parse_allequal(elem: ET.Element, constraint_id: Optional[str], model: Model) -> AllEqualConstraint:
    """Parse allEqual constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    elif elem.text:
        variables = _parse_variable_list(elem.text.strip(), model)
    else:
        variables = []

    return AllEqualConstraint(id=constraint_id, variables=variables)


def _parse_ordered(elem: ET.Element, constraint_id: Optional[str], model: Model) -> OrderedConstraint:
    """Parse ordered constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    elif elem.text:
        variables = _parse_variable_list(elem.text.strip(), model)
    else:
        variables = []

    operator = elem.get("operator", "le")

    return OrderedConstraint(id=constraint_id, variables=variables, operator=operator)


def _parse_sum(elem: ET.Element, constraint_id: Optional[str], model: Model) -> SumConstraint:
    """Parse sum constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    elif elem.text and not elem.find("coeffs") and not elem.find("condition"):
        variables = _parse_variable_list(elem.text.strip(), model)
    else:
        variables = []

    coeffs_elem = elem.find("coeffs")
    coefficients = []
    if coeffs_elem is not None and coeffs_elem.text:
        coefficients = [int(c.strip()) for c in coeffs_elem.text.strip().split()]

    condition_elem = elem.find("condition")
    condition = None
    if condition_elem is not None and condition_elem.text:
        condition = _parse_condition(condition_elem.text.strip())

    return SumConstraint(
        id=constraint_id,
        variables=variables,
        coefficients=coefficients,
        condition=condition
    )


def _parse_count(elem: ET.Element, constraint_id: Optional[str], model: Model) -> CountConstraint:
    """Parse count constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    else:
        variables = []

    values_elem = elem.find("values")
    value = 0
    if values_elem is not None and values_elem.text:
        value = int(values_elem.text.strip())

    condition_elem = elem.find("condition")
    condition = None
    if condition_elem is not None and condition_elem.text:
        condition = _parse_condition(condition_elem.text.strip())

    return CountConstraint(
        id=constraint_id,
        variables=variables,
        value=value,
        condition=condition
    )


def _parse_nvalues(elem: ET.Element, constraint_id: Optional[str], model: Model) -> NValuesConstraint:
    """Parse nValues constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    else:
        variables = []

    condition_elem = elem.find("condition")
    condition = None
    if condition_elem is not None and condition_elem.text:
        condition = _parse_condition(condition_elem.text.strip())

    return NValuesConstraint(id=constraint_id, variables=variables, condition=condition)


def _parse_cardinality(elem: ET.Element, constraint_id: Optional[str], model: Model) -> CardinalityConstraint:
    """Parse cardinality (GCC) constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    else:
        variables = []

    values_elem = elem.find("values")
    values = []
    if values_elem is not None and values_elem.text:
        values = [int(v.strip()) for v in values_elem.text.strip().split()]

    occurs_elem = elem.find("occurs")
    occurrences = []
    if occurs_elem is not None and occurs_elem.text:
        for part in occurs_elem.text.strip().split():
            try:
                occurrences.append(int(part))
            except ValueError:
                occurrences.append(part)  # Variable name

    return CardinalityConstraint(
        id=constraint_id,
        variables=variables,
        values=values,
        occurrences=occurrences
    )


def _parse_element(elem: ET.Element, constraint_id: Optional[str], model: Model) -> ElementConstraint:
    """Parse element constraint."""
    list_elem = elem.find("list")
    array_name = ""
    if list_elem is not None and list_elem.text:
        array_name = list_elem.text.strip()

    index_elem = elem.find("index")
    index = ""
    if index_elem is not None and index_elem.text:
        index = index_elem.text.strip()

    value_elem = elem.find("value")
    value = 0
    if value_elem is not None and value_elem.text:
        try:
            value = int(value_elem.text.strip())
        except ValueError:
            value = value_elem.text.strip()

    return ElementConstraint(id=constraint_id, array=array_name, index=index, value=value)


def _parse_minmax(elem: ET.Element, constraint_id: Optional[str], model: Model, is_min: bool) -> MinMaxConstraint:
    """Parse minimum/maximum constraint."""
    list_elem = elem.find("list")
    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
    else:
        variables = []

    condition_elem = elem.find("condition")
    condition = None
    if condition_elem is not None and condition_elem.text:
        condition = _parse_condition(condition_elem.text.strip())

    return MinMaxConstraint(
        id=constraint_id,
        type=ConstraintType.MINIMUM if is_min else ConstraintType.MAXIMUM,
        variables=variables,
        condition=condition
    )


def _parse_channel(elem: ET.Element, constraint_id: Optional[str], model: Model) -> ChannelConstraint:
    """Parse channel constraint."""
    lists = elem.findall("list")
    list1 = []
    list2 = []

    if len(lists) >= 2:
        if lists[0].text:
            list1 = _parse_variable_list(lists[0].text.strip(), model)
        if lists[1].text:
            list2 = _parse_variable_list(lists[1].text.strip(), model)

    return ChannelConstraint(id=constraint_id, list1=list1, list2=list2)


def _parse_group(elem: ET.Element, model: Model) -> list[Constraint]:
    """Parse a group of constraints with template."""
    constraints = []
    for child in elem:
        if child.tag == "args":
            continue
        constraint = _parse_constraint(child, model)
        if constraint:
            if isinstance(constraint, list):
                constraints.extend(constraint)
            else:
                constraints.append(constraint)
    return constraints


def _parse_block(elem: ET.Element, model: Model) -> list[Constraint]:
    """Parse a block of constraints."""
    constraints = []
    for child in elem:
        constraint = _parse_constraint(child, model)
        if constraint:
            if isinstance(constraint, list):
                constraints.extend(constraint)
            else:
                constraints.append(constraint)
    return constraints


def _parse_condition(condition_str: str) -> Condition:
    """Parse condition string like '(le,100)' or '(in,1..10)'."""
    # Remove parentheses
    condition_str = condition_str.strip()
    if condition_str.startswith("(") and condition_str.endswith(")"):
        condition_str = condition_str[1:-1]

    parts = condition_str.split(",", 1)
    if len(parts) != 2:
        return Condition(operator=ConditionOperator.EQ, operand=0)

    op_str = parts[0].strip().lower()
    operand_str = parts[1].strip()

    # Map operator
    op_map = {
        "lt": ConditionOperator.LT,
        "le": ConditionOperator.LE,
        "gt": ConditionOperator.GT,
        "ge": ConditionOperator.GE,
        "eq": ConditionOperator.EQ,
        "ne": ConditionOperator.NE,
        "in": ConditionOperator.IN,
        "notin": ConditionOperator.NOTIN,
    }
    operator = op_map.get(op_str, ConditionOperator.EQ)

    # Parse operand
    if ".." in operand_str:
        # Range
        parts = operand_str.split("..")
        operand = (int(parts[0]), int(parts[1]))
    else:
        try:
            operand = int(operand_str)
        except ValueError:
            operand = operand_str  # Variable name

    return Condition(operator=operator, operand=operand)


def _parse_variable_list(list_str: str, model: Model) -> list[str]:
    """Parse variable list, expanding array references like 'x[]' or 'y[0..2]'."""
    variables = []
    parts = list_str.replace(",", " ").split()

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check for array expansion: x[] means all elements of array x
        if part.endswith("[]"):
            arr_name = part[:-2]
            arr = _find_array(arr_name, model)
            if arr:
                for i in range(arr.get_total_size()):
                    variables.append(f"{arr_name}[{i}]")
            else:
                variables.append(part)
        elif "[" in part and ".." in part:
            # Range expansion: x[0..2] -> x[0], x[1], x[2]
            match = re.match(r"(\w+)\[(\d+)\.\.(\d+)\]", part)
            if match:
                arr_name = match.group(1)
                start = int(match.group(2))
                end = int(match.group(3))
                for i in range(start, end + 1):
                    variables.append(f"{arr_name}[{i}]")
            else:
                variables.append(part)
        else:
            variables.append(part)

    return variables


def _find_array(name: str, model: Model) -> Optional[Array]:
    """Find an array by name in the model."""
    for arr in model.arrays:
        if arr.id == name:
            return arr
    return None


def _parse_objectives(elem: ET.Element, model: Model) -> None:
    """Parse objectives section."""
    for child in elem:
        if child.tag in ("minimize", "maximize"):
            obj = _parse_objective(child, child.tag == "minimize", model)
            if obj:
                model.objectives.append(obj)


def _parse_objective(elem: ET.Element, minimize: bool, model: Model) -> Optional[Objective]:
    """Parse a single objective."""
    obj_type_str = elem.get("type", "expression")
    type_map = {
        "expression": ObjectiveType.EXPRESSION,
        "sum": ObjectiveType.SUM,
        "product": ObjectiveType.PRODUCT,
        "minimum": ObjectiveType.MINIMUM,
        "maximum": ObjectiveType.MAXIMUM,
        "nvalues": ObjectiveType.NVALUES,
        "lex": ObjectiveType.LEX,
    }
    obj_type = type_map.get(obj_type_str, ObjectiveType.EXPRESSION)

    # Check for list element
    list_elem = elem.find("list")
    coeffs_elem = elem.find("coeffs")

    if list_elem is not None and list_elem.text:
        variables = _parse_variable_list(list_elem.text.strip(), model)
        coefficients = []
        if coeffs_elem is not None and coeffs_elem.text:
            coefficients = [int(c.strip()) for c in coeffs_elem.text.strip().split()]

        return Objective(
            type=obj_type,
            minimize=minimize,
            variables=variables,
            coefficients=coefficients
        )
    elif elem.text:
        # Direct expression or variable list
        text = elem.text.strip()
        if obj_type == ObjectiveType.EXPRESSION:
            expr = _convert_expression(text, model)
            return Objective(type=obj_type, minimize=minimize, expression=expr)
        else:
            variables = _parse_variable_list(text, model)
            return Objective(type=obj_type, minimize=minimize, variables=variables)

    return None
