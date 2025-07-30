import logging  # noqa

from dictlist2 import DictList2


class TestDistinct:
    """
    Набор тестов для метода `distinct()` класса DictList2.

    Тесты покрывают следующие случаи:
    1. Уникальность по всем ключам (по умолчанию).
    2. Уникальность по одному указанному полю.
    3. Уникальность по нескольким полям.
    4. Поведение с пустым списком.
    5. Поведение при одинаковых значениях и разных дополнительных ключах.
    """

    def test_distinct_all_fields(self):
        """Проверка уникальности по всем полям"""
        data = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        )
        expected = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        assert data.distinct() == expected

    def test_distinct_by_single_key(self):
        """Проверка уникальности по одному полю"""
        data = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Alice"},
                {"id": 3, "name": "Bob"},
            ]
        )
        expected = [{"name": "Alice"}, {"name": "Bob"}]
        assert data.distinct(by="name") == expected

    def test_distinct_by_multiple_keys(self):
        """Проверка уникальности по нескольким полям"""
        data = DictList2(
            [
                {"id": 1, "project": "A", "name": "Anna"},
                {"id": 2, "project": "A", "name": "Anna"},
                {"id": 3, "project": "B", "name": "Anna"},
            ]
        )
        expected = [
            {"project": "A", "name": "Anna"},
            {"project": "B", "name": "Anna"},
        ]
        assert data.distinct(by=["project", "name"]) == expected

    def test_distinct_empty_list(self):
        """Проверка работы метода на пустом списке"""
        data = DictList2([])
        assert data.distinct() == []

    def test_distinct_ignores_extra_fields(self):
        """Проверка, что уникальность по полю игнорирует остальные ключи"""
        data = DictList2(
            [
                {"id": 1, "name": "Alice", "extra": "x"},
                {"id": 2, "name": "Alice", "extra": "y"},
                {"id": 3, "name": "Bob", "extra": "z"},
            ]
        )
        expected = [{"name": "Alice"}, {"name": "Bob"}]
        assert data.distinct(by="name") == expected

    def test_distinct_by_none_value(self):
        """Проверка уникальности по нескольким полям"""
        data = DictList2(
            [
                {"id": 1, "project": "A", "name": "Anna"},
                {"id": 2, "project": None, "name": "Anna"},
                {"id": 3, "project": "B", "name": "Anna"},
            ]
        )
        expected = [
            {"project": None},
            {"project": "A"},
            {"project": "B"},
        ]
        assert data.distinct(by=["project"]) == expected
