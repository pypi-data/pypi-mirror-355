# Polytruth - Multi-valued Logic Truth Value Computation Framework

`Polytruth` is a Python package for modeling and computing truth values in multi-valued logic systems. It supports complex logical expressions, variable management, rule-based reasoning, and external file parsing, making it ideal for  multi-valued logic applications. 

The name "Polytruth" combines "poly-" (many) with "truth", emphasizing its ability to handle multiple truth values beyond simple binary logic.

## Features
- 🧠 Support for n-valued logic systems (n ≥ 2)

- 📝 Logical expression parsing and evaluation

- 🔧 Customizable logical operators


- 📁 External file loading for logic rules

- 🚀 NumPy-based vector operations

## Installation
```bash
pip install polytruth
```

## Quick Start
### Basic Usage
```python

import numpy as np
from polytruth import LogicSystem, MultiValuedOperators,And, Not

# Initialize logic system with poly-valued operators
logic_system = LogicSystem(MultiValuedOperators())

# Create variables with multi-dimensional truth values
a = logic_system.new_variable("a", np.array([0.3, 0.7]))  # Ternary logic example
b = logic_system.new_variable("b", np.array([0.5, 0.5]))  # Probability distribution

# Add logical rules
rule1 = And(And(a, b), Not(b))
logic_system.add_rule("rule1", rule1)
logic_system.add_rule("rule2", ~a & (b | a))

# Set variable values
logic_system.set_variable_values({
    "is(a,c)": np.array([0.5, 0.9]),  # Custom predicate
    "b": 0.8  # Scalar truth value
})

# Compute all rules
print("All rule computations:")
print(logic_system.compute())

# Compute specific rule
print("\nSingle rule computation:")
print(logic_system.compute("rule1"))

# View all variables
print("\nSystem variables:")
print(logic_system.variables)
## View all rules
print("\nSystem rules:")
print(logic_system.rules)
```
### File Parsing

```python
from polytruth.parser import parse_file
from polytruth import LogicSystem, MultiValuedOperators
logic_system = LogicSystem(MultiValuedOperators())
parse_file("data.logic",logic_system)
print(logic_system.rules)
```
### File Format Example (data.logic)
```
test : is(a,c)&b
test2 : ~a -> b
```
## Supported Operators

|Operator|Class (in code)|Symbol (in file)|Example|Description|
|--|--|--|--|--|
|Conjunction|And|`&`, `∧`,`/\` |a & b|Logical AND|
|Disjunction|Or|`∨`, `\/`| a\|b |Logical OR|
|Negation|Not|`~`, `¬`|~a|Logical NOT|
|Implication|Implies|`->`,`→`|a -> b|Material implication|
|Equivalence|Equiv|`<->`,`↔`|a <-> b|Logical equivalence|
