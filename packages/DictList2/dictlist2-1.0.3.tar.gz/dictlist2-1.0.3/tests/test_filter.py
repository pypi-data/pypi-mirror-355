import logging  # noqa

from dictlist2 import DictList2


class TestDictList2Filter:
    """
    Тесты для метода `filter()` класса DictList2.

    Проверяются следующие сценарии:

    1. Простая фильтрация по одному полю.
    2. Фильтрация по нескольким полям.
    3. Сортировка результата по одному ключу.
    4. Сортировка результата по нескольким ключам.
    5. Фильтрация без совпадений.
    6. Поведение с пустым исходным списком.
    """

    def test_filter_by_single_field(self):
        """Фильтрация по одному полю"""
        data = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Alice"},
            ]
        )
        result = data.filter(where={"name": "Alice"})
        expected = [
            {"id": 1, "name": "Alice"},
            {"id": 3, "name": "Alice"},
        ]
        assert result == expected

    def test_filter_by_multiple_fields(self):
        """Фильтрация по нескольким полям"""
        data = DictList2(
            [
                {"id": 1, "name": "Alice", "role": "Admin"},
                {"id": 2, "name": "Alice", "role": "User"},
                {"id": 3, "name": "Bob", "role": "User"},
            ]
        )
        result = data.filter(where={"name": "Alice", "role": "User"})
        expected = [{"id": 2, "name": "Alice", "role": "User"}]
        assert result == expected

    def test_filter_with_sort_by_single_key(self):
        """Фильтрация и сортировка по одному полю"""
        data = DictList2(
            [
                {"id": 3, "name": "Alice"},
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        )
        result = data.filter(where={"name": "Alice"}, order="id")
        expected = [
            {"id": 1, "name": "Alice"},
            {"id": 3, "name": "Alice"},
        ]
        assert result == expected

    def test_filter_with_sort_by_multiple_keys(self):
        """Фильтрация и сортировка по нескольким ключам"""
        data = DictList2(
            [
                {"name": "Alice", "age": 30},
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 20},
            ]
        )
        result = data.filter(where={"name": "Alice"}, order=["name", "age"])
        expected = [
            {"name": "Alice", "age": 25},
            {"name": "Alice", "age": 30},
        ]
        assert result == expected

    def test_filter_no_matches(self):
        """Фильтрация без совпадений"""
        data = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        )
        result = data.filter(where={"name": "Charlie"})
        assert result == []

    def test_filter_empty_list(self):
        """Фильтрация при пустом списке"""
        data = DictList2([])
        result = data.filter(where={"name": "Alice"})
        assert result == []
