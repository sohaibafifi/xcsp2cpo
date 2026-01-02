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

# Convert LZMA-compressed file
xcsp2cpo problem.xml.lzma

# Convert to file
xcsp2cpo problem.xml -o problem.cpo

# From stdin
cat problem.xml | xcsp2cpo -

# Verbose mode
xcsp2cpo problem.xml -v

# Show all warnings (unsupported features)
python -W always main.py problem.xml
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

## Architecture

The converter uses a transformation pipeline inspired by [CPMpy](https://github.com/CPMpy/cpmpy):

```
[XCSP3 XML / XML.LZMA]
        |
        v
    parser.py --> IR Model (model.py)
        |
        v
    transformations/
      |-- normalize.py    (expand arrays, flatten groups)
      |-- decompose.py    (convert unsupported constraints)
      +-- rewrite.py      (normalize expressions)
        |
        v
    writer.py --> CPO Output
```

### Transformation Pipeline

Unsupported constraints are automatically decomposed into equivalent supported forms:

| Constraint | Decomposition |
|------------|---------------|
| `allEqual(x, y, z)` | `x == y; x == z;` |
| `ordered([x, y, z], le)` | `x <= y; y <= z;` |
| `channel(list1, list2)` | Pairwise inverse constraints |

## Supported Features

### File Formats

| Format | Status |
|--------|--------|
| `.xml` | Supported |
| `.xml.lzma` | Supported |

### Variables

| XCSP3 | CPO | Status |
|-------|-----|--------|
| `<var>` with domain | `intVar(domain)` | Supported |
| `<array>` 1D | `[intVar(...), ...]` | Supported |
| `<array>` multi-dimensional | Flattened array | Supported |
| Domain ranges (`1..10`) | `1..10` | Supported |
| Domain enumeration (`0 1 2`) | `0, 1, 2` | Supported |
| Symbolic domains | - | Not supported (warning) |

### Constraints

| XCSP3 | CPO | Transformation |
|-------|-----|----------------|
| `intension` | Infix expression | direct |
| `extension` (supports) | `allowedAssignments()` | direct |
| `extension` (conflicts) | `forbiddenAssignments()` | direct |
| `allDifferent` | `alldiff()` | direct |
| `allEqual` | Pairwise `==` | decompose |
| `ordered` | Comparison chain | decompose |
| `sum` | Linear expression | direct |
| `count` | `count()` | direct |
| `nValues` | `numberOfDifferentValues()` | direct |
| `cardinality` | `distribute()` | direct |
| `minimum` | `min()` | direct |
| `maximum` | `max()` | direct |
| `element` | `element()` | direct |
| `channel` | Pairwise constraints | decompose |

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

Unsupported features will generate warnings during conversion.

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
| `symbolic` | String/symbolic domains |
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

## Python API

```python
from xcsp2cpo.converter import convert_to_cpo, convert_file

# Convert XML string
cpo_output = convert_to_cpo(xml_content)

# Convert file (supports .xml and .xml.lzma)
cpo_output = convert_file("problem.xml.lzma")

# Convert and write to file
convert_file("input.xml.lzma", output_path="output.cpo")

# Disable transformation pipeline (use legacy mode)
cpo_output = convert_to_cpo(xml_content, use_transformations=False)
```

## References

- [XCSP3 Specifications](https://xcsp.org/specifications/)
- [IBM CP Optimizer File Format](https://www.ibm.com/docs/en/icos/22.1.2?topic=manual-cp-optimizer-file-format-syntax)
- [CPMpy](https://github.com/CPMpy/cpmpy) - Inspiration for transformation architecture

## License

MIT License. See `LICENSE`.
