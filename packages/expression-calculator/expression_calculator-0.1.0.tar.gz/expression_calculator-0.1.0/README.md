# Expression Calculator

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![PyPI Version](https://img.shields.io/pypi/v/expression-calculator)](https://pypi.org/project/expression-calculator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A secure mathematical expression evaluator with lexical analysis that doesn't use unsafe `eval()`

## Key Features

✅ **Safe parsing** - No dangerous `eval()` usage  
✅ Parentheses and operator precedence support  
✅ Integer and floating-point arithmetic  
✅ Detailed error reporting  
✅ Clean modular architecture  

## Installation

```bash
pip install expression_calculator
```

## Usage
```python
from expression_calculator import Calculator

calc = Calculator()
result = calc.calculate("(5 + 3) * 2 - 10 / 2")  # Returns 11.0
print(f"Result: {result}")
```
## Supported Operations

| Operator | Example |
|----------|:--------|
|  `plus` `+`  | `2 + 3 + 2`  |
| `minus` `-` | `8 - 3 - 2` |
| `multiply` `*` | `9 * 5 * 2` |
| `divide` `/` | `6 / 2 / 1.4` |
| `parens` `()` | `5 + (3 * 2)`|

## Credits
🖥 - `Discord`: **`@exityxdev`**
📱 - `Telegram`: **`@exityx`**

## Thanks You! ❤