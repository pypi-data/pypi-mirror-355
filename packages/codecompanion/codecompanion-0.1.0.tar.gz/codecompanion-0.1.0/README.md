# CodeCompanion

**CodeCompanion** is your smart code analysis buddy for Python. It analyzes functions and provides suggestions for improvement, code quality, documentation, PEP8 formatting, complexity, and more.

## 🚀 Features

- Auto-formatting using `black` and `autopep8`
- Dead code detection using `pyflakes`
- Cyclomatic complexity analysis using `radon`
- Docstring parsing and summarization
- Type hint extraction
- Variable usage analysis
- Autocomplete suggestions using `jedi`

## 📦 Installation

```bash
pip install codecompanion
git clone https://github.com/yourname/codecompanion.git
cd codecompanion
pip install -e .

## Usage Example

from codecompanion.core import CodeCompanion

def example(x: int, y: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    result = x + y
    return result

cc = CodeCompanion(example)

print(cc.get_function_summary())
print(cc.get_pep8_suggestions())
print(cc.get_black_suggestion())
print(cc.check_dead_code())
print(cc.get_complexity_report())
print(cc.get_raw_metrics())
print(cc.get_type_hints())
print(cc.get_variable_analysis())
print(cc.get_autocomplete_suggestions('res'))
     

