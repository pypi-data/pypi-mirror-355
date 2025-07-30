import logging  # noqa
import pytest

from dictlist2 import DictList2


class TestDictList2LeftJoin:
    """
    Тесты метода `left_join()` класса DictList2.

    Проверяемые сценарии:
    ---------------------
    1. Полное совпадение по ключу — поля из right добавляются к left.
    2. Несовпадающий элемент в left остаётся без изменений.
    3. Лишние элементы в right игнорируются.
    4. Перекрывающиеся ключи не затираются (оставляются из left).
    5. Если в right отсутствует ключ — выбрасывается KeyError.
    """

    def test_left_join_basic(self):
        """
        ✅ Совпадения по ключу объединяются, несовпадения из left сохраняются.
        """
        left = DictList2(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ]
        )
        right = [
            {"id": 1, "role": "Admin"},
            {"id": 2, "role": "User"},
            {"id": 4, "role": "Guest"},
        ]
        result = left.left_join(right, key="id")
        assert result == [
            {"id": 1, "name": "Alice", "role": "Admin"},
            {"id": 2, "name": "Bob", "role": "User"},
            {"id": 3, "name": "Charlie"},
        ]

    def test_left_join_no_match(self):
        """
        ✅ Если совпадений в right нет — элементы left не меняются.
        """
        left = DictList2(
            [
                {"id": 1},
            ]
        )
        right = [
            {"id": 2, "role": "User"},
        ]
        result = left.left_join(right, key="id")
        assert result == [{"id": 1}]

    def test_left_join_overlap_keys(self):
        """
        ✅ Если ключ из right уже есть в left — сохраняется значение из left.
        """
        left = DictList2(
            [
                {"id": 1, "role": "Boss"},
            ]
        )
        right = [
            {"id": 1, "role": "Admin"},
        ]
        result = left.left_join(right, key="id")
        assert result == [{"id": 1, "role": "Boss"}]

    def test_left_join_extra_right_fields(self):
        """
        ✅ Лишние поля из right добавляются, если их нет в left.
        """
        left = DictList2(
            [
                {"id": 1},
            ]
        )
        right = [
            {"id": 1, "x": 100, "y": 200},
        ]
        result = left.left_join(right, key="id")
        assert result == [{"id": 1, "x": 100, "y": 200}]

    def test_left_join_missing_key_in_right(self):
        """
        ❗ Если в right нет ключа — выбрасывается KeyError.
        """
        left = DictList2(
            [
                {"id": 1},
            ]
        )
        right = [
            {"uuid": 1, "role": "Admin"},  # нет 'id'
        ]
        with pytest.raises(KeyError):
            left.left_join(right, key="id")
