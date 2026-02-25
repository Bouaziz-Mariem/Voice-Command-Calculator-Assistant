"""
Safe Math Evaluator Module
Evaluates math expression strings using an AST whitelist approach.
Only allows basic arithmetic, exponentiation, and a set of safe math functions.

Why not eval()?
    eval("23 * 47") works, but eval("__import__('os').system('rm -rf /')") also works.
    This module walks the AST and only permits known-safe node types.

Example:
    evaluate("23 * 47")    → 1081
    evaluate("sqrt(144)")  → 12.0
    evaluate("-5 + 3")     → -2
"""

import ast
import math
import operator


# Whitelisted binary and unary operators
SAFE_OPERATORS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.Mod:  operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Whitelisted functions (name → callable)
SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs":  abs,
    "round": round,
}

# Cap exponent to prevent huge computations like 999 ** 999999
MAX_EXPONENT = 1000


def evaluate(expression: str) -> float | int:
    """
    Safely evaluate a math expression string.

    Args:
        expression: A string like "23 * 47" or "sqrt(144)".

    Returns:
        The numeric result.

    Raises:
        ValueError: If the expression contains unsupported operations.
        ZeroDivisionError: If division by zero is attempted.
    """
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def _eval_node(node):
    """Recursively evaluate an AST node, only allowing safe operations."""

    # Literal number (int or float)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    # Binary operation: left op right
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        # Guard against huge exponents
        if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)):
            if abs(right) > MAX_EXPONENT:
                raise ValueError(f"Exponent too large: {right} (max {MAX_EXPONENT})")
        return op_func(left, right)

    # Unary operation: -x or +x
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_func = SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(operand)

    # Function call: sqrt(144), abs(-5)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(f"Unsupported call: {ast.dump(node)}")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unsupported function: {func_name}")
        args = [_eval_node(arg) for arg in node.args]
        return SAFE_FUNCTIONS[func_name](*args)

    raise ValueError(f"Unsupported expression: {ast.dump(node)}")
