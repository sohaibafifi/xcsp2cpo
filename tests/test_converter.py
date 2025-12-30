"""Tests for XCSP to CPO converter."""

import pytest
from pathlib import Path

from xcsp2cpo.converter import convert_to_cpo, convert_file
from xcsp2cpo.parser import parse_xcsp


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestConvertToCpo:
    """Test CPO conversion."""

    def test_convert_simple_csp(self):
        """Test converting simple CSP."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 1..10 </var>
            <var id="y"> 1..10 </var>
          </variables>
          <constraints>
            <allDifferent> x y </allDifferent>
          </constraints>
        </instance>
        """
        cpo = convert_to_cpo(xml)
        assert "intVar(1..10)" in cpo
        assert "alldiff([x, y])" in cpo

    def test_convert_sum_constraint(self):
        """Test converting sum constraint."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 0..10 </var>
            <var id="y"> 0..10 </var>
          </variables>
          <constraints>
            <sum>
              <list> x y </list>
              <coeffs> 2 3 </coeffs>
              <condition> (le,20) </condition>
            </sum>
          </constraints>
        </instance>
        """
        cpo = convert_to_cpo(xml)
        assert "2*x + 3*y <= 20" in cpo

    def test_convert_intension(self):
        """Test converting intension constraint."""
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
        cpo = convert_to_cpo(xml)
        assert "(x < y)" in cpo

    def test_convert_extension(self):
        """Test converting extension constraint."""
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
        cpo = convert_to_cpo(xml)
        assert "allowedAssignments" in cpo

    def test_convert_optimization(self):
        """Test converting optimization problem."""
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
        cpo = convert_to_cpo(xml)
        assert "maximize" in cpo


class TestConvertFile:
    """Test file conversion."""

    def test_convert_simple_csp_file(self):
        """Test converting simple CSP file."""
        cpo = convert_file(FIXTURES_DIR / "simple_csp.xml")
        assert "alldiff" in cpo
        assert "intVar" in cpo

    def test_convert_array_example_file(self):
        """Test converting array example file."""
        cpo = convert_file(FIXTURES_DIR / "array_example.xml")
        assert "alldiff" in cpo

    def test_convert_sum_constraint_file(self):
        """Test converting sum constraint file."""
        cpo = convert_file(FIXTURES_DIR / "sum_constraint.xml")
        assert "<=" in cpo

    def test_convert_optimization_file(self):
        """Test converting optimization file."""
        cpo = convert_file(FIXTURES_DIR / "optimization.xml")
        assert "maximize" in cpo

    def test_convert_intension_file(self):
        """Test converting intension file."""
        cpo = convert_file(FIXTURES_DIR / "intension.xml")
        assert "<" in cpo or ">" in cpo

    def test_convert_extension_file(self):
        """Test converting extension file."""
        cpo = convert_file(FIXTURES_DIR / "extension.xml")
        assert "allowedAssignments" in cpo


class TestExpressionConversion:
    """Test expression conversion."""

    def test_convert_add(self):
        """Test converting add expression."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 0..10 </var>
            <var id="y"> 0..10 </var>
            <var id="z"> 0..10 </var>
          </variables>
          <constraints>
            <intension> eq(add(x,y),z) </intension>
          </constraints>
        </instance>
        """
        cpo = convert_to_cpo(xml)
        assert "((x + y) == z)" in cpo

    def test_convert_nested_expression(self):
        """Test converting nested expression."""
        xml = """
        <instance format="XCSP3" type="CSP">
          <variables>
            <var id="x"> 0..10 </var>
            <var id="y"> 0..10 </var>
            <var id="z"> 0..10 </var>
          </variables>
          <constraints>
            <intension> lt(add(x,y),mul(z,2)) </intension>
          </constraints>
        </instance>
        """
        cpo = convert_to_cpo(xml)
        assert "(x + y)" in cpo
        assert "(z * 2)" in cpo
        assert "<" in cpo
