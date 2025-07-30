import pytest
from ppe import ppe_debug


def test_custom_message():
    @ppe_debug
    def test_func():
        x = 10 + 5  ## Adding two numbers
        return x

    result = test_func()
    assert result == 15


def test_statement_echo():
    @ppe_debug
    def test_func():
        x = 10 + 5  ## -
        return x

    result = test_func()
    assert result == 15


def test_variable_inspection():
    @ppe_debug
    def test_func():
        a = 1  ## @a
        b = 2  ## @after:b
        c = a + b  ## @before:a,b
        d = 10  ## @before:d
        return c

    result = test_func()
    assert result == 3