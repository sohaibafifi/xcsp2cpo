"""Tests for XCSP3 parser."""

import pytest
from pathlib import Path

from xcsp2cpo.parser import parse_xcsp, parse_xcsp_file
from xcsp2cpo.model import ProblemType, ConstraintType


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParseVariables:
    """Test variable parsing."""

    def test_parse_single_var(self):
        """Test parsing a single variable."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 1..10 </var>
          </variables>
          <constraints></constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.variables) == 1
        assert model.variables[0].id == "x"
        assert model.variables[0].domain.ranges == [(1, 10)]

    def test_parse_multiple_vars(self):
        """Test parsing multiple variables."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 1..10 </var>
            <var id="y"> 0..5 </var>
          </variables>
          <constraints></constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.variables) == 2

    def test_parse_array(self):
        """Test parsing array of variables."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <array id="x" size="[5]"> 0..4 </array>
          </variables>
          <constraints></constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.arrays) == 1
        assert model.arrays[0].id == "x"
        assert model.arrays[0].size == [5]


class TestParseConstraints:
    """Test constraint parsing."""

    def test_parse_alldifferent(self):
        """Test parsing allDifferent constraint."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 1..3 </var>
            <var id="y"> 1..3 </var>
            <var id="z"> 1..3 </var>
          </variables>
          <constraints>
            <allDifferent> x y z </allDifferent>
          </constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.constraints) == 1
        assert model.constraints[0].type == ConstraintType.ALLDIFFERENT

    def test_parse_sum(self):
        """Test parsing sum constraint."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <array id="x" size="[3]"> 0..10 </array>
          </variables>
          <constraints>
            <sum>
              <list> x[] </list>
              <condition> (le,10) </condition>
            </sum>
          </constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.constraints) == 1
        assert model.constraints[0].type == ConstraintType.SUM

    def test_parse_intension(self):
        """Test parsing intension constraint."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 1..10 </var>
            <var id="y"> 1..10 </var>
          </variables>
          <constraints>
            <intension> lt(x,y) </intension>
          </constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.constraints) == 1
        assert model.constraints[0].type == ConstraintType.INTENSION

    def test_parse_extension(self):
        """Test parsing extension constraint."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 0..1 </var>
            <var id="y"> 0..1 </var>
          </variables>
          <constraints>
            <extension>
              <list> x y </list>
              <supports> (0,1)(1,0) </supports>
            </extension>
          </constraints>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.constraints) == 1
        assert model.constraints[0].type == ConstraintType.EXTENSION


class TestParseObjectives:
    """Test objective parsing."""

    def test_parse_minimize(self):
        """Test parsing minimize objective."""
        xml = """
        <instance format="XCSP3" type="COP">
          <variables>
            <array id="x" size="[3]"> 0 1 </array>
          </variables>
          <constraints></constraints>
          <objectives>
            <minimize type="sum">
              <list> x[] </list>
            </minimize>
          </objectives>
        </instance>
        """
        model = parse_xcsp(xml)
        assert model.problem_type == ProblemType.COP
        assert len(model.objectives) == 1
        assert model.objectives[0].minimize is True

    def test_parse_maximize(self):
        """Test parsing maximize objective."""
        xml = """
        <instance format="XCSP3" type="COP">
          <variables>
            <var id="x"> 0..100 </var>
          </variables>
          <constraints></constraints>
          <objectives>
            <maximize type="expression"> x </maximize>
          </objectives>
        </instance>
        """
        model = parse_xcsp(xml)
        assert len(model.objectives) == 1
        assert model.objectives[0].minimize is False


class TestParseFile:
    """Test parsing from files."""

    def test_parse_simple_csp(self):
        """Test parsing simple CSP file."""
        model = parse_xcsp_file(FIXTURES_DIR / "simple_csp.xml")
        assert len(model.variables) == 3
        assert len(model.constraints) == 1

    def test_parse_array_example(self):
        """Test parsing array example file."""
        model = parse_xcsp_file(FIXTURES_DIR / "array_example.xml")
        assert len(model.arrays) == 1
        assert model.arrays[0].size == [5]

    def test_parse_optimization(self):
        """Test parsing optimization file."""
        model = parse_xcsp_file(FIXTURES_DIR / "optimization.xml")
        assert model.problem_type == ProblemType.COP
        assert len(model.objectives) == 1
