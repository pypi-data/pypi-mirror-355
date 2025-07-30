# Инструкция по загрузке на PyPI

## Что мы сделали:

✅ Создали пакет `simple-math-calijaaa` с математическими функциями  
✅ Настроили структуру проекта согласно стандартам Python  
✅ Создали все необходимые файлы (pyproject.toml, README.md, LICENSE)  
✅ Протестировали код локально  
✅ Собрали дистрибутивы пакета  
✅ Загрузили на TestPyPI для тестирования  
✅ Успешно установили и протестировали пакет  

## Загрузка на настоящий PyPI:

### 1. Зарегистрируйтесь на PyPI
- Перейдите на https://pypi.org/account/register/
- Создайте аккаунт и подтвердите email

### 2. Создайте API токен
- Перейдите на https://pypi.org/manage/account/#api-tokens
- Создайте новый токен с правами "Entire account"
- **ВАЖНО**: Сохраните токен, он больше не будет показан!

### 3. Загрузите пакет
```bash
# Удалите тестовую версию (если установлена)
python3 -m pip uninstall simple-math-calijaaa

# Загрузите на настоящий PyPI
python3 -m twine upload dist/*
```

При запросе токена вставьте ваш API токен (включая префикс `pypi-`).

### 4. Проверьте результат
После успешной загрузки ваш пакет будет доступен на:
https://pypi.org/project/simple-math-calijaaa/

### 5. Установите с настоящего PyPI
```bash
python3 -m pip install simple-math-calijaaa
```

## Использование пакета:

```python
from simple_math_calijaaa.calculator import add_numbers, factorial, fibonacci

# Примеры использования
print(f"5 + 3 = {add_numbers(5, 3)}")
print(f"5! = {factorial(5)}")
print(f"10-е число Фибоначчи: {fibonacci(10)}")
```

## Функции пакета:
- `add_numbers(a, b)` - сложение
- `multiply_numbers(a, b)` - умножение  
- `power_of_two(number)` - возведение в квадрат
- `factorial(n)` - факториал числа
- `is_even(number)` - проверка четности
- `fibonacci(n)` - n-е число Фибоначчи

## Важные заметки:
- Имя пакета должно быть уникальным на PyPI
- TestPyPI - это временное хранилище для тестирования
- Обязательно тестируйте пакет локально перед загрузкой 