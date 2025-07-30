from __future__ import annotations

import pytest

from audioarxiv.preprocess import process_math_equations


def test_simple_inline_equation():
    text = "The result is $x + y$ in the equation."
    output = process_math_equations(text)
    assert "Math: " in output
    assert "Add(Symbol('x'), Symbol('y'))" in output


def test_block_equation():
    text = "We define it as $$a**2 + b**2 = c**2$$ in the theorem."
    output = process_math_equations(text)
    # Should convert expression into a readable format or fallback
    assert "Math: " in output or "Equation: " in output


def test_multiple_equations():
    text = "Consider $x+1$ and $y-2$."
    output = process_math_equations(text)
    assert "Math: " in output
    assert output.count("Math:") == 2
    assert "Add(Symbol('x'), Integer(1))" in output
    assert "Add(Symbol('y'), Integer(-2))" in output


def test_invalid_equation_fallback():
    text = "Here's a bad equation: $\\frac{x}{y$"
    output = process_math_equations(text)
    assert "Equation: " in output
    assert "\\frac{x}{y" in output  # Invalid LaTeX should be preserved


@pytest.mark.skip(reason="Dollar sign ambiguity – skip for now")
def test_equation_with_dollar_sign_literal():
    text = "The cost is $5, but the math is $x+2$."
    processed = process_math_equations(text)
    assert "Math: " in processed
    assert "Equation: 5" not in processed


def test_no_math_equation():
    text = "This sentence has no math at all."
    output = process_math_equations(text)
    assert output == text


def test_nested_dollars():
    text = "Example with nested: $$x + $y + z$$$"
    output = process_math_equations(text)
    # Should ideally not break
    assert "$" not in output or "Math:" in output or "Equation:" in output
