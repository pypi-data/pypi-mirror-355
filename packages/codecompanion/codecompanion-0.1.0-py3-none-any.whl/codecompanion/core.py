import ast
import inspect
import textwrap
from typing import List, Dict, Any

import autopep8
import pyflakes.api
import pyflakes.reporter
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
import black
import docstring_parser
import jedi
import io
import sys

class CodeCompanion:
    def __init__(self, func):
        self.func = func
        self.source = textwrap.dedent(inspect.getsource(func))
        self.tree = ast.parse(self.source)

    def get_function_summary(self) -> Dict[str, Any]:
        """
        Extracts metadata and summary from the function.
        """
        docstring = inspect.getdoc(self.func)
        parsed = docstring_parser.parse(docstring) if docstring else None
        return {
            "name": self.func.__name__,
            "args": list(inspect.signature(self.func).parameters.keys()),
            "docstring": docstring,
            "description": parsed.short_description if parsed else None,
        }

    def get_pep8_suggestions(self) -> str:
        """
        Returns PEP8-formatted code suggestion using autopep8.
        """
        return autopep8.fix_code(self.source)

    def get_black_suggestion(self) -> str:
        """
        Returns code formatted with Black.
        """
        return black.format_str(self.source, mode=black.Mode())

    def check_dead_code(self) -> str:
        """
        Run pyflakes and return any warnings or unused code.
        """
        out = io.StringIO()
        reporter = pyflakes.reporter.Reporter(out, out)
        pyflakes.api.check(self.source, self.func.__name__, reporter=reporter)
        return out.getvalue()

    def get_complexity_report(self) -> List[Dict[str, Any]]:
        """
        Get cyclomatic complexity of function using radon.
        """
        results = radon_cc.cc_visit(self.source)
        return [r._asdict() for r in results]

    def get_raw_metrics(self) -> Dict[str, Any]:
        """
        Return raw metrics from radon.
        """
        return radon_metrics.mi_visit(self.source, True)

    def get_type_hints(self) -> Dict[str, str]:
        """
        Return type hints for function.
        """
        return {k: str(v.annotation) for k, v in inspect.signature(self.func).parameters.items() if v.annotation != inspect.Parameter.empty}

    def get_variable_analysis(self) -> List[str]:
        """
        List all variable names used in function.
        """
        return list({node.id for node in ast.walk(self.tree) if isinstance(node, ast.Name)})

    def get_autocomplete_suggestions(self, prefix: str) -> List[str]:
        """
        Get Jedi autocomplete suggestions for a prefix.
        """
        script = jedi.Script(self.source + f"\n{prefix}")
        return [comp.name for comp in script.complete()]

# Example use
if __name__ == "__main__":
    def sample_function(x: int, y: int) -> int:
        """Add two numbers.
        
        Returns the sum of x and y.
        """
        z = x + y
        unused_var = 42
        return z

    companion = CodeCompanion(sample_function)

    print("Function Summary:", companion.get_function_summary())
    print("PEP8 Suggestion:\n", companion.get_pep8_suggestions())
    print("Black Formatting:\n", companion.get_black_suggestion())
    print("Dead Code Warnings:\n", companion.check_dead_code())
    print("Cyclomatic Complexity:\n", companion.get_complexity_report())
    print("Raw Metrics:", companion.get_raw_metrics())
    print("Type Hints:", companion.get_type_hints())
    print("Variables:", companion.get_variable_analysis())
    print("Autocomplete Suggestions for 'z':", companion.get_autocomplete_suggestions('z'))
