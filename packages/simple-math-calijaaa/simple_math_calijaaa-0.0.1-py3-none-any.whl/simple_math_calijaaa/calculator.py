"""
Простой модуль для математических операций.
"""

def add_numbers(a, b):
    """Сложение двух чисел."""
    return a + b

def multiply_numbers(a, b):
    """Умножение двух чисел."""
    return a * b

def power_of_two(number):
    """Возведение числа в квадрат."""
    return number ** 2

def factorial(n):
    """Вычисление факториала числа."""
    if n < 0:
        raise ValueError("Факториал не определен для отрицательных чисел")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def is_even(number):
    """Проверка, является ли число четным."""
    return number % 2 == 0

def fibonacci(n):
    """Вычисление n-го числа Фибоначчи."""
    if n < 0:
        raise ValueError("n должно быть неотрицательным")
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b 