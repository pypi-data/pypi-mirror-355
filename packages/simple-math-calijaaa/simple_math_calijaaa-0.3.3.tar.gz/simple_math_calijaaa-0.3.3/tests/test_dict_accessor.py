"""Тесты для модуля dict_accessor."""

import sys
sys.path.insert(0, '../src')

from simple_math_calijaaa.dict_accessor import get_value, get_categories, get_items_in_category

def test_get_value_success():
    """Тест успешного получения значений из встроенного словаря."""
    # Тестируем новые категории и элементы
    result1 = get_value("3", "1")
    assert isinstance(result1, str) and len(result1) > 0
    
    result2 = get_value("3", "2")
    assert isinstance(result2, str) and len(result2) > 0
    
    result3 = get_value("4", "1")
    assert isinstance(result3, str) and len(result3) > 0

def test_get_value_key_error():
    """Тест ошибок с неверными ключами."""
    # Несуществующая категория
    try:
        get_value("несуществующая_категория", "1")
        assert False, "Должна была возникнуть KeyError"
    except KeyError as e:
        assert "не найдена" in str(e)
        assert "Доступные категории" in str(e)
    
    # Несуществующий элемент в существующей категории
    try:
        get_value("3", "несуществующий_элемент")
        assert False, "Должна была возникнуть KeyError"
    except KeyError as e:
        assert "не найден в категории" in str(e)
        assert "Доступные элементы" in str(e)

def test_get_value_type_error():
    """Тест ошибок типов."""
    # Тест с неправильными типами ключей
    try:
        get_value(123, "1")
        assert False, "Должна была возникнуть TypeError"
    except TypeError:
        pass
    
    try:
        get_value("3", 456)
        assert False, "Должна была возникнуть TypeError"
    except TypeError:
        pass

def test_get_categories():
    """Тест получения списка категорий."""
    categories = get_categories()
    
    assert isinstance(categories, list)
    assert len(categories) > 0
    # Проверяем что все категории - строки
    for category in categories:
        assert isinstance(category, str)

def test_get_items_in_category():
    """Тест получения элементов в категории."""
    # Тестируем категорию 3
    items_3 = get_items_in_category("3")
    
    assert isinstance(items_3, list)
    assert len(items_3) > 0
    for item in items_3:
        assert isinstance(item, str)
    
    # Тестируем категорию 4
    items_4 = get_items_in_category("4")
    
    assert isinstance(items_4, list)
    assert len(items_4) > 0
    for item in items_4:
        assert isinstance(item, str)

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