import logging  # noqa
import pytest

from dictlist2 import DictList2


class TestDictList2Join:
    """
    Тесты для метода `join()` класса DictList2.

    Сценарии:
    ---------
    1. Inner join по ключу с совпадением.
    2. Нет совпадений — пустой результат.
    3. Совпадает часть записей.
    4. Проверка сохранения всех полей из обоих словарей.
    5. Ключ отсутствует в одном из словарей — игнорируется.
    """

    def test_full_match_join(self):
        """Inner join, когда все ключи совпадают"""
        left = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        )
        right = [
            {"id": 1, "role": "Admin"},
            {"id": 2, "role": "User"},
        ]
        result = left.join(right, key="id")
        assert len(result) == 2
        assert result[0]["role"] == "Admin"
        assert result[1]["role"] == "User"

    def test_partial_match_join(self):
        """Inner join, когда часть ключей совпадает"""
        left = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        )
        right = [
            {"id": 1, "role": "Admin"},
            {"id": 3, "role": "Guest"},
        ]
        result = left.join(right, key="id")
        assert len(result) == 1
        assert result[0] == {"id": 1, "name": "Alice", "role": "Admin"}

    def test_no_match(self):
        """Inner join, когда нет совпадений по ключу"""
        left = DictList2(
            [
                {"id": 10, "name": "Zoe"},
            ]
        )
        right = [
            {"id": 1, "role": "Admin"},
        ]
        result = left.join(right, key="id")
        assert result == []

    def test_merge_fields_correctly(self):
        """Проверка, что все поля объединены"""
        left = DictList2(
            [
                {"id": 1, "a": 100},
            ]
        )
        right = [
            {"id": 1, "b": 200},
        ]
        result = left.join(right, key="id")
        assert result == [{"id": 1, "a": 100, "b": 200}]

    def test_missing_key_in_right(self):
        """
        ❗ ОШИБКА ОЖИДАЕМА:
        Если в правом списке нет нужного ключа — ожидается KeyError.
        """
        left = DictList2(
            [
                {"id": 1},
            ]
        )
        right = [
            {"uuid": 1, "role": "Admin"},  # 'id' отсутствует
        ]
        with pytest.raises(KeyError):
            left.join(right, key="id")
