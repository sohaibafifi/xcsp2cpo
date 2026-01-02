"""Tests for the transformation pipeline."""

import pytest

from xcsp2cpo.parser import parse_xcsp
from xcsp2cpo.transformations import transform, CPO_SUPPORTED_CONSTRAINTS
from xcsp2cpo.transformations.normalize import normalize, expand_array_reference
from xcsp2cpo.transformations.decompose import (
    decompose_unsupported,
    decompose_allequal,
    decompose_ordered,
    decompose_channel,
)
from xcsp2cpo.model import (
    IntensionConstraint, AllEqualConstraint, OrderedConstraint,
    ChannelConstraint, ConstraintType,
)


class TestNormalize:
    """Test normalization transformations."""

    def test_expand_array_reference_full(self):
        """Test expanding full array reference."""
        result = expand_array_reference("x[]", {"x": [3]})
        assert result == ["x[0]", "x[1]", "x[2]"]

    def test_expand_array_reference_range(self):
        """Test expanding range reference."""
        result = expand_array_reference("x[1..3]", {"x": [5]})
        assert result == ["x[1]", "x[2]", "x[3]"]

    def test_expand_array_reference_indexed(self):
        """Test indexed reference passes through."""
        result = expand_array_reference("x[2]", {"x": [5]})
        assert result == ["x[2]"]

    def test_expand_array_reference_plain_var(self):
        """Test plain variable passes through."""
        result = expand_array_reference("x", {})
        assert result == ["x"]


class TestDecomposeAllEqual:
    """Test allEqual decomposition."""

    def test_decompose_allequal_basic(self):
        """Test basic allEqual decomposition."""
        constraint = AllEqualConstraint(
            variables=["x", "y", "z"]
        )
        result = decompose_allequal(constraint)

        assert len(result) == 2
        assert all(isinstance(c, IntensionConstraint) for c in result)
        assert result[0].expression == "x == y"
        assert result[1].expression == "x == z"

    def test_decompose_allequal_two_vars(self):
        """Test allEqual with two variables."""
        constraint = AllEqualConstraint(
            variables=["a", "b"]
        )
        result = decompose_allequal(constraint)

        assert len(result) == 1
        assert result[0].expression == "a == b"

    def test_decompose_allequal_single_var(self):
        """Test allEqual with single variable returns empty."""
        constraint = AllEqualConstraint(
            variables=["x"]
        )
        result = decompose_allequal(constraint)
        assert len(result) == 0


class TestDecomposeOrdered:
    """Test ordered decomposition."""

    def test_decompose_ordered_le(self):
        """Test ordered with <= operator."""
        constraint = OrderedConstraint(
            variables=["x", "y", "z"],
            operator="le"
        )
        result = decompose_ordered(constraint)

        assert len(result) == 2
        assert result[0].expression == "x <= y"
        assert result[1].expression == "y <= z"

    def test_decompose_ordered_lt(self):
        """Test ordered with < operator."""
        constraint = OrderedConstraint(
            variables=["a", "b", "c"],
            operator="lt"
        )
        result = decompose_ordered(constraint)

        assert len(result) == 2
        assert result[0].expression == "a < b"
        assert result[1].expression == "b < c"

    def test_decompose_ordered_ge(self):
        """Test ordered with >= operator."""
        constraint = OrderedConstraint(
            variables=["x", "y"],
            operator="ge"
        )
        result = decompose_ordered(constraint)

        assert len(result) == 1
        assert result[0].expression == "x >= y"


class TestDecomposeChannel:
    """Test channel decomposition."""

    def test_decompose_channel_basic(self):
        """Test basic channel decomposition."""
        constraint = ChannelConstraint(
            list1=["x[0]", "x[1]"],
            list2=["y[0]", "y[1]"]
        )
        result = decompose_channel(constraint)

        # 2x2 = 4 pairwise constraints
        assert len(result) == 4
        assert all(isinstance(c, IntensionConstraint) for c in result)

        # Check structure of expressions
        expressions = [c.expression for c in result]
        assert "(x[0] == 0) == (y[0] == 0)" in expressions
        assert "(x[0] == 1) == (y[1] == 0)" in expressions


class TestTransformPipeline:
    """Test full transformation pipeline."""

    def test_transform_allequal(self):
        """Test pipeline with allEqual constraint."""
        xcsp = '''<?xml version="1.0" encoding="UTF-8"?>
        <instance format="XCSP3" type="CSP">
          <variables>
            <array id="x" size="[3]"> 1..10 </array>
          </variables>
          <constraints>
            <allEqual>
              <list> x[] </list>
            </allEqual>
          </constraints>
        </instance>
        '''
        model = parse_xcsp(xcsp)
        assert len(model.constraints) == 1
        assert model.constraints[0].type == ConstraintType.ALLEQUAL

        transformed = transform(model)
        # allEqual of 3 vars → 2 pairwise equality constraints
        assert len(transformed.constraints) == 2
        assert all(c.type == ConstraintType.INTENSION for c in transformed.constraints)

    def test_transform_ordered(self):
        """Test pipeline with ordered constraint."""
        xcsp = '''<?xml version="1.0" encoding="UTF-8"?>
        <instance format="XCSP3" type="CSP">
          <variables>
            <array id="x" size="[4]"> 1..10 </array>
          </variables>
          <constraints>
            <ordered operator="lt">
              <list> x[] </list>
            </ordered>
          </constraints>
        </instance>
        '''
        model = parse_xcsp(xcsp)
        transformed = transform(model)

        # ordered of 4 vars → 3 comparison constraints
        assert len(transformed.constraints) == 3
        assert all(c.type == ConstraintType.INTENSION for c in transformed.constraints)

    def test_transform_preserves_supported(self):
        """Test that supported constraints are preserved."""
        xcsp = '''<?xml version="1.0" encoding="UTF-8"?>
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 1..10 </var>
            <var id="y"> 1..10 </var>
          </variables>
          <constraints>
            <allDifferent> x y </allDifferent>
            <sum>
              <list> x y </list>
              <condition> (le,15) </condition>
            </sum>
          </constraints>
        </instance>
        '''
        model = parse_xcsp(xcsp)
        transformed = transform(model)

        # Both alldifferent and sum are supported, should be preserved
        assert len(transformed.constraints) == 2
        types = {c.type for c in transformed.constraints}
        assert ConstraintType.ALLDIFFERENT in types
        assert ConstraintType.SUM in types

    def test_transform_mixed_constraints(self):
        """Test pipeline with mix of supported and unsupported constraints."""
        xcsp = '''<?xml version="1.0" encoding="UTF-8"?>
        <instance format="XCSP3" type="CSP">
          <variables>
            <array id="x" size="[3]"> 1..10 </array>
          </variables>
          <constraints>
            <allDifferent>
              <list> x[] </list>
            </allDifferent>
            <allEqual>
              <list> x[] </list>
            </allEqual>
          </constraints>
        </instance>
        '''
        model = parse_xcsp(xcsp)
        assert len(model.constraints) == 2

        transformed = transform(model)
        # alldifferent preserved, allEqual decomposed to 2
        assert len(transformed.constraints) == 3

        types = [c.type for c in transformed.constraints]
        assert types.count(ConstraintType.ALLDIFFERENT) == 1
        assert types.count(ConstraintType.INTENSION) == 2


class TestSupportedConstraintsRegistry:
    """Test the supported constraints registry."""

    def test_registry_contains_basic_constraints(self):
        """Test that registry contains expected constraints."""
        assert "alldifferent" in CPO_SUPPORTED_CONSTRAINTS
        assert "sum" in CPO_SUPPORTED_CONSTRAINTS
        assert "count" in CPO_SUPPORTED_CONSTRAINTS
        assert "element" in CPO_SUPPORTED_CONSTRAINTS
        assert "intension" in CPO_SUPPORTED_CONSTRAINTS
        assert "extension" in CPO_SUPPORTED_CONSTRAINTS

    def test_registry_excludes_decomposable(self):
        """Test that decomposable constraints are not in supported."""
        assert "allequal" not in CPO_SUPPORTED_CONSTRAINTS
        assert "ordered" not in CPO_SUPPORTED_CONSTRAINTS
        assert "channel" not in CPO_SUPPORTED_CONSTRAINTS
