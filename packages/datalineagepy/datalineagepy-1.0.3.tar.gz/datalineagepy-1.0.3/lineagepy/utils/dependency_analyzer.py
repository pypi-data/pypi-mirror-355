"""
Utility functions for analyzing function dependencies and column references.
"""

import ast
import inspect
import re
from typing import Set, List, Optional, Callable, Any


def extract_column_references(func: Callable, available_columns: List[str]) -> Set[str]:
    """
    Extract column references from a function by analyzing its source code.

    Args:
        func: Function to analyze
        available_columns: List of available column names

    Returns:
        Set of column names that the function likely references
    """
    try:
        # Get function source code
        source = inspect.getsource(func)

        # Extract column references using multiple methods
        referenced_columns = set()

        # Method 1: Look for string literals that match column names
        string_literals = re.findall(r'["\']([^"\']+)["\']', source)
        for literal in string_literals:
            if literal in available_columns:
                referenced_columns.add(literal)

        # Method 2: Look for bracket notation (df['column'])
        bracket_refs = re.findall(r'\[[\'"](.*?)[\'"]\]', source)
        for ref in bracket_refs:
            if ref in available_columns:
                referenced_columns.add(ref)

        # Method 3: Look for dot notation (x.column, df.column)
        dot_refs = re.findall(r'\.(\w+)', source)
        for ref in dot_refs:
            if ref in available_columns:
                referenced_columns.add(ref)

        # Method 4: AST analysis for more sophisticated detection
        try:
            tree = ast.parse(source)
            visitor = ColumnReferenceVisitor(available_columns)
            visitor.visit(tree)
            referenced_columns.update(visitor.referenced_columns)
        except:
            pass  # Fall back to regex methods if AST parsing fails

        return referenced_columns

    except (OSError, TypeError):
        # If we can't get source code, return all columns as conservative estimate
        return set(available_columns)


def analyze_function_dependencies(func: Callable, available_columns: List[str]) -> dict:
    """
    Analyze a function to determine its column dependencies.

    Args:
        func: Function to analyze
        available_columns: List of available column names

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'referenced_columns': set(),
        'confidence': 'low',
        'method': 'fallback',
        'all_columns_assumed': False
    }

    try:
        # Try to get function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        # If function takes DataFrame as parameter, analyze source
        if len(params) == 1:
            referenced_cols = extract_column_references(
                func, available_columns)

            if referenced_cols:
                analysis['referenced_columns'] = referenced_cols
                analysis['confidence'] = 'medium'
                analysis['method'] = 'source_analysis'
            else:
                # Conservative fallback - assume all columns
                analysis['referenced_columns'] = set(available_columns)
                analysis['confidence'] = 'low'
                analysis['method'] = 'conservative_fallback'
                analysis['all_columns_assumed'] = True
        else:
            # Function doesn't take DataFrame parameter
            analysis['referenced_columns'] = set()
            analysis['confidence'] = 'high'
            analysis['method'] = 'no_dataframe_param'

    except Exception:
        # Ultimate fallback
        analysis['referenced_columns'] = set(available_columns)
        analysis['confidence'] = 'low'
        analysis['method'] = 'error_fallback'
        analysis['all_columns_assumed'] = True

    return analysis


class ColumnReferenceVisitor(ast.NodeVisitor):
    """AST visitor to find column references in function source code."""

    def __init__(self, available_columns: List[str]):
        self.available_columns = set(available_columns)
        self.referenced_columns = set()

    def visit_Subscript(self, node):
        """Visit subscript nodes (e.g., df['column'])."""
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            if node.slice.value in self.available_columns:
                self.referenced_columns.add(node.slice.value)
        elif isinstance(node.slice, ast.Str):  # Python < 3.8 compatibility
            if node.slice.s in self.available_columns:
                self.referenced_columns.add(node.slice.s)

        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Visit attribute nodes (e.g., df.column)."""
        if isinstance(node.attr, str) and node.attr in self.available_columns:
            self.referenced_columns.add(node.attr)

        self.generic_visit(node)

    def visit_Str(self, node):
        """Visit string nodes."""
        if node.s in self.available_columns:
            self.referenced_columns.add(node.s)

        self.generic_visit(node)

    def visit_Constant(self, node):
        """Visit constant nodes (Python 3.8+)."""
        if isinstance(node.value, str) and node.value in self.available_columns:
            self.referenced_columns.add(node.value)

        self.generic_visit(node)


def analyze_lambda_expression(lambda_str: str, available_columns: List[str]) -> Set[str]:
    """
    Analyze a lambda expression string to find column references.

    Args:
        lambda_str: String representation of lambda expression
        available_columns: List of available column names

    Returns:
        Set of referenced column names
    """
    referenced_columns = set()

    # Look for bracket notation
    bracket_refs = re.findall(r'\[[\'"](.*?)[\'"]\]', lambda_str)
    for ref in bracket_refs:
        if ref in available_columns:
            referenced_columns.add(ref)

    # Look for dot notation
    dot_refs = re.findall(r'\.(\w+)', lambda_str)
    for ref in dot_refs:
        if ref in available_columns:
            referenced_columns.add(ref)

    return referenced_columns


def smart_column_dependency_detection(func_or_expr: Any, available_columns: List[str]) -> Set[str]:
    """
    Smart detection of column dependencies from various function types.

    Args:
        func_or_expr: Function, lambda, or expression to analyze
        available_columns: List of available column names

    Returns:
        Set of referenced column names
    """
    if callable(func_or_expr):
        analysis = analyze_function_dependencies(
            func_or_expr, available_columns)
        return analysis['referenced_columns']
    elif isinstance(func_or_expr, str):
        return analyze_lambda_expression(func_or_expr, available_columns)
    else:
        # Unknown type - conservative fallback
        return set(available_columns)
