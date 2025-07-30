# 🔄 Обновленная Dict Library - Руководство по использованию

## 🎯 Что изменилось

Мы полностью обновили библиотеку! Теперь вместо математических функций у нас есть:

**Основная функция**: `get_nested_value(data_dict, key1, key2)`
- Принимает словарь словарей и два строковых ключа
- Возвращает значение по пути `[key1][key2]`
- Включает проверки типов и понятные ошибки

## 📁 Структура проекта

```
packaging_tutorial/
├── src/simple_math_calijaaa/
│   ├── __init__.py                    # Версия 0.1.0
│   └── dict_accessor.py               # Основной модуль
├── tests/
│   └── test_dict_accessor.py          # Тесты
├── dist/                              # Новые дистрибутивы v0.1.0
├── pyproject.toml                     # Обновленная конфигурация
├── README.md                          # Обновленное описание
└── LICENSE
```

## 🚀 Использование

### Базовый пример:
```python
from simple_math_calijaaa.dict_accessor import get_nested_value

# Ваши данные
my_data = {
    "студенты": {
        "иван": "отличник",
        "мария": "хорошист"
    },
    "преподаватели": {
        "петров": "математика",
        "сидоров": "физика"
    }
}

# Получаем значения
student_grade = get_nested_value(my_data, "студенты", "иван")
teacher_subject = get_nested_value(my_data, "преподаватели", "петров")

print(f"Иван - {student_grade}")           # Иван - отличник
print(f"Петров ведет {teacher_subject}")   # Петров ведет математика
```

### Использование встроенных данных:
```python
from simple_math_calijaaa.dict_accessor import get_nested_value, SAMPLE_DATA

# Встроенные примеры
print("=== Примеры встроенных данных ===")
print(f"Админ: {get_nested_value(SAMPLE_DATA, 'пользователи', 'admin')}")
print(f"Язык: {get_nested_value(SAMPLE_DATA, 'настройки', 'язык')}")
print(f"Москва: {get_nested_value(SAMPLE_DATA, 'города', 'москва')}")
```

### Обработка ошибок:
```python
try:
    value = get_nested_value(my_data, "несуществующий", "ключ")
except KeyError as e:
    print(f"Ошибка: {e}")

try:
    value = get_nested_value("не словарь", "ключ1", "ключ2")
except TypeError as e:
    print(f"Ошибка типа: {e}")
```

## 🧪 Тестирование

```bash
# Запуск тестов
cd tests
python3 test_dict_accessor.py
```

## 📦 Сборка и публикация

```bash
# Удаление старой версии пакета (если установлена)
python3 -m pip uninstall simple-math-calijaaa

# Сборка новой версии
python3 -m build

# Загрузка на TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Установка и тестирование
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps simple-math-calijaaa
```

## ✅ Проверка работы

После установки:
```python
from simple_math_calijaaa.dict_accessor import get_nested_value, SAMPLE_DATA

# Быстрый тест
result = get_nested_value(SAMPLE_DATA, "пользователи", "admin")
print(f"Результат: {result}")  # Должно быть: Администратор
```

## 🔗 Полезные ссылки

- **TestPyPI**: https://test.pypi.org/project/simple-math-calijaaa/
- **Версия**: 0.1.0
- **Тип**: Dict Library (работа со словарями)

---

**Готово к продакшену!** 🎉 Ваша библиотека теперь специализируется на работе с вложенными словарями. 