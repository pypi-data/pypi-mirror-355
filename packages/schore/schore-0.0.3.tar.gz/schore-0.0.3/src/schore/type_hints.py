from typing import TypeVar

scalar_types = (int, float, str, bool)
"""Tuple of scalar-like types: int, float, str, bool"""

ScalarT = TypeVar("ScalarT", int, float, str, bool)
"""TypeVar for scalar-like types: int, float, str, bool"""

numeric_types = (int, float)
"""Tuple of numeric types: int and float"""

NumericT = TypeVar("NumericT", int, float)
"""TypeVar for numeric types: int and float"""
