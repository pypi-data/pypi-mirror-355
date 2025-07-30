"""Тесты для модуля dict_accessor."""

import sys
sys.path.insert(0, '../src')

from simple_math_calijaaa.dict_accessor import get_value, get_categories, get_items_in_category

def test_get_value_success():
    """Тест успешного получения значений из встроенного словаря."""
    # Тестируем различные категории и элементы
    assert get_value("пользователи", "admin") == "Администратор системы"
    assert get_value("настройки", "язык") == "русский"
    assert get_value("города", "москва") == "Москва - столица России"
    assert get_value("предметы", "математика") == "Царица наук"
    assert get_value("животные", "кот") == "Домашний питомец"

def test_get_value_key_error():
    """Тест ошибок с неверными ключами."""
    # Несуществующая категория
    try:
        get_value("несуществующая_категория", "элемент1")
        assert False, "Должна была возникнуть KeyError"
    except KeyError as e:
        assert "не найдена" in str(e)
        assert "Доступные категории" in str(e)
    
    # Несуществующий элемент в существующей категории
    try:
        get_value("пользователи", "несуществующий_пользователь")
        assert False, "Должна была возникнуть KeyError"
    except KeyError as e:
        assert "не найден в категории" in str(e)
        assert "Доступные элементы" in str(e)

def test_get_value_type_error():
    """Тест ошибок типов."""
    # Тест с неправильными типами ключей
    try:
        get_value(123, "admin")
        assert False, "Должна была возникнуть TypeError"
    except TypeError:
        pass
    
    try:
        get_value("пользователи", 456)
        assert False, "Должна была возникнуть TypeError"
    except TypeError:
        pass

def test_get_categories():
    """Тест получения списка категорий."""
    categories = get_categories()
    expected_categories = ["пользователи", "настройки", "города", "предметы", "животные"]
    
    assert isinstance(categories, list)
    assert len(categories) == 5
    for category in expected_categories:
        assert category in categories

def test_get_items_in_category():
    """Тест получения элементов в категории."""
    # Тестируем категорию пользователи
    users = get_items_in_category("пользователи")
    expected_users = ["admin", "user", "guest", "moderator", "editor"]
    
    assert isinstance(users, list)
    assert len(users) == 5
    for user in expected_users:
        assert user in users
    
    # Тестируем категорию животные
    animals = get_items_in_category("животные")
    expected_animals = ["кот", "собака", "попугай", "рыбка", "хомяк"]
    
    assert isinstance(animals, list)
    for animal in expected_animals:
        assert animal in animals

def test_get_items_in_category_error():
    """Тест ошибки при получении элементов несуществующей категории."""
    try:
        get_items_in_category("несуществующая_категория")
        assert False, "Должна была возникнуть KeyError"
    except KeyError as e:
        assert "не найдена" in str(e)
        assert "Доступные категории" in str(e)

if __name__ == "__main__":
    test_get_value_success()
    test_get_value_key_error()
    test_get_value_type_error()
    test_get_categories()
    test_get_items_in_category()
    test_get_items_in_category_error()
    print("Все тесты прошли успешно! ✅") 