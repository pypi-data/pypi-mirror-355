"""Тесты для модуля calculator."""

import sys
sys.path.insert(0, '../src')

from simple_math_calijaaa.calculator import (
    add_numbers, multiply_numbers, power_of_two, 
    factorial, is_even, fibonacci
)

def test_add_numbers():
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_multiply_numbers():
    assert multiply_numbers(2, 3) == 6
    assert multiply_numbers(-2, 3) == -6
    assert multiply_numbers(0, 5) == 0

def test_power_of_two():
    assert power_of_two(3) == 9
    assert power_of_two(0) == 0
    assert power_of_two(-2) == 4

def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120

def test_is_even():
    assert is_even(2) == True
    assert is_even(3) == False
    assert is_even(0) == True

def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55

if __name__ == "__main__":
    test_add_numbers()
    test_multiply_numbers()
    test_power_of_two()
    test_factorial()
    test_is_even()
    test_fibonacci()
    print("Все тесты прошли успешно! ✅") 