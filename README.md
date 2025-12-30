# xcsp2cpo

Convert XCSP3 constraint satisfaction problems to IBM CP Optimizer (CPO) file format.

## Installation

```bash
pip install -e .
```

Or run directly:

```bash
python main.py input.xml
```

## Usage

```bash
# Convert to stdout
xcsp2cpo problem.xml

# Convert to file
xcsp2cpo problem.xml -o problem.cpo

# From stdin
cat problem.xml | xcsp2cpo -

# Verbose mode
xcsp2cpo problem.xml -v
```

## Example

**Input (XCSP3):**
```xml
<instance format="XCSP3" type="COP">
  <variables>
    <array id="x" size="[5]"> 0 1 </array>
  </variables>
  <constraints>
    <sum>
      <list> x[] </list>
      <coeffs> 11 24 5 23 16 </coeffs>
      <condition> (le,100) </condition>
    </sum>
  </constraints>
  <objectives>
    <maximize type="sum">
      <list> x[] </list>
      <coeffs> 46 46 38 88 3 </coeffs>
    </maximize>
  </objectives>
</instance>
```

**Output (CPO):**
```
// Variables
x = [intVar(0, 1), intVar(0, 1), intVar(0, 1), intVar(0, 1), intVar(0, 1)];

// Constraints
11*x[0] + 24*x[1] + 5*x[2] + 23*x[3] + 16*x[4] <= 100;

// Objective
maximize(46*x[0] + 46*x[1] + 38*x[2] + 88*x[3] + 3*x[4]);
```

## Supported Features

### Variables

| XCSP3 | CPO | Status |
|-------|-----|--------|
| `<var>` with domain | `intVar(domain)` | Supported |
| `<array>` 1D | `[intVar(...), ...]` | Supported |
| `<array>` multi-dimensional | Flattened array | Supported |
| Domain ranges (`1..10`) | `1..10` | Supported |
| Domain enumeration (`0 1 2`) | `0, 1, 2` | Supported |

### Constraints

| XCSP3 | CPO | Status |
|-------|-----|--------|
| `intension` | Infix expression | Supported |
| `extension` (supports) | `allowedAssignments()` | Supported |
| `extension` (conflicts) | `forbiddenAssignments()` | Supported |
| `allDifferent` | `alldiff()` | Supported |
| `allDifferent` with except | `alldiff()` | Partial |
| `allEqual` | Pairwise `==` | Supported |
| `ordered` | Comparison chain | Supported |
| `sum` | Linear expression | Supported |
| `count` | `count()` | Supported |
| `nValues` | `numberOfDifferentValues()` | Supported |
| `cardinality` | `distribute()` | Supported |
| `minimum` | `min()` | Supported |
| `maximum` | `max()` | Supported |
| `element` | `element()` | Supported |
| `channel` | Pairwise constraints | Supported |

### Objectives

| XCSP3 | CPO | Status |
|-------|-----|--------|
| `minimize` | `minimize()` | Supported |
| `maximize` | `maximize()` | Supported |
| Type: expression | Direct expression | Supported |
| Type: sum | `sum()` or linear | Supported |
| Type: product | Product expression | Supported |
| Type: minimum/maximum | `min()`/`max()` | Supported |

### Intension Operators

| XCSP3 | CPO |
|-------|-----|
| `add(x,y)` | `x + y` |
| `sub(x,y)` | `x - y` |
| `mul(x,y)` | `x * y` |
| `div(x,y)` | `x / y` |
| `mod(x,y)` | `x % y` |
| `neg(x)` | `-x` |
| `abs(x)` | `abs(x)` |
| `lt`, `le`, `gt`, `ge`, `eq`, `ne` | `<`, `<=`, `>`, `>=`, `==`, `!=` |
| `and`, `or`, `not` | `&&`, `\|\|`, `!` |
| `imp(a,b)` | `a => b` |
| `if(c,t,e)` | Conditional |
| `min`, `max` | `min()`, `max()` |
| `dist(x,y)` | `abs(x - y)` |

## Not Yet Supported

### Constraints

| XCSP3 | Notes |
|-------|-------|
| `regular` | Finite automaton constraint |
| `mdd` | Multi-valued decision diagram |
| `cumulative` | Scheduling constraint |
| `noOverlap` | Scheduling constraint |
| `circuit` | Hamiltonian circuit |
| `path` | Path constraint |
| `tree` | Tree constraint |
| `stretch` | Sequence constraint |
| `binPacking` | Bin packing |
| `knapsack` | Knapsack constraint |

### Variable Types

| XCSP3 | Notes |
|-------|-------|
| `realVar` | Real/continuous variables |
| `setVar` | Set variables |
| `graphVar` | Graph variables |
| `qualVar` | Qualitative variables |

### Problem Types

| XCSP3 | Notes |
|-------|-------|
| WCSP | Weighted CSP |
| QCSP | Quantified CSP |
| DisCSP | Distributed CSP |
| Multi-objective | Multiple objectives |

## References

- [XCSP3 Specifications](https://xcsp.org/specifications/)
- [IBM CP Optimizer File Format](https://www.ibm.com/docs/en/icos/22.1.2?topic=manual-cp-optimizer-file-format-syntax)

## License

MIT
