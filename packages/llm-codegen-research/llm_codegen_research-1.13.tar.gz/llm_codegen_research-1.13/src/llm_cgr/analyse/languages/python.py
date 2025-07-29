"""Utility functions for Python code analysis."""

import ast
import sys

from llm_cgr.analyse.languages.code_data import CodeData


PYTHON_STDLIB = getattr(
    sys, "stdlib_module_names", []
)  # use this below to categorise packages


class PythonAnalyser(ast.NodeVisitor):
    def __init__(self):
        self.defined_funcs: set[str] = set()
        self.called_funcs: set[str] = set()
        self.stdlibs: set[str] = set()
        self.packages: set[str] = set()
        self.imports: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # save defined functions
        self.defined_funcs.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func = node.func

        # save `foo()` function calls
        if isinstance(func, ast.Name):
            self.called_funcs.add(func.id)

        # save `lib.method()` function calls
        elif isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                self.called_funcs.add(f"{func.value.id}.{func.attr}")
            else:
                self.called_funcs.add(func.attr)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        # save `import module` imports
        for alias in node.names:
            # save all imports
            self.imports.add(alias.name)

            # save packages
            top_level = alias.name.split(".")[0]
            if top_level in PYTHON_STDLIB:
                self.stdlibs.add(top_level)
            else:
                self.packages.add(top_level)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # save `from module import thing` imports
        module = node.module or ""

        # save packages
        # node.level is 0 for absolute imports, 1+ for relative imports
        if module and node.level == 0:
            package = module.split(".")[0]
            if package in PYTHON_STDLIB:
                self.stdlibs.add(package)
            else:
                self.packages.add(package)

        # save all imports
        for alias in node.names:
            full = f"{module}.{alias.name}" if module else alias.name
            self.imports.add(full)

        self.generic_visit(node)


def analyse_python_code(code: str) -> CodeData:
    """
    Analyse Python code to extract functions and imports.
    """
    tree = ast.parse(code)
    analyser = PythonAnalyser()
    analyser.visit(tree)
    return CodeData(
        valid=True,
        defined_funcs=analyser.defined_funcs,
        called_funcs=analyser.called_funcs,
        stdlibs=analyser.stdlibs,
        packages=analyser.packages,
        imports=analyser.imports,
    )
