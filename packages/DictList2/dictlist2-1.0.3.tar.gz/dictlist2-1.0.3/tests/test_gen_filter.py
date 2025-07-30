import logging  # noqa

from dictlist2 import DictList2


class TestDictList2GenFilter:
    """
    Тесты для метода `gen_filter()` класса DictList2.

    Сценарии:
    ---------
    1. Группировка по одному полю.
    2. Группировка по нескольким полям.
    3. Сортировка внутри группы по одному полю.
    4. Сортировка внутри группы по нескольким полям.
    5. Сортировка по словарю с направлениями ('asc', 'desc').
    6. Обработка пустого списка.
    """

    def test_group_by_single_field(self):
        """Группировка по одному полю"""
        data = DictList2(
            [
                {"user": "Alice", "hours": 2},
                {"user": "Bob", "hours": 3},
                {"user": "Alice", "hours": 1},
            ]
        )
        result = list(data.gen_filter(by="user"))
        assert len(result) == 2
        keys = [group[0]["user"] for group in result]
        assert set(keys) == {"Alice", "Bob"}

    def test_group_by_multiple_fields(self):
        """Группировка по нескольким полям"""
        data = DictList2(
            [
                {"project": "A", "user": "Alice"},
                {"project": "A", "user": "Bob"},
                {"project": "A", "user": "Alice"},
            ]
        )
        result = list(data.gen_filter(by=["project", "user"]))
        assert len(result) == 2
        expected_keys = [
            {"project": "A", "user": "Alice"},
            {"project": "A", "user": "Bob"},
        ]
        actual_keys = [group[0] for group in result]
        assert actual_keys == expected_keys

    def test_sort_within_group_by_single_key(self):
        """Сортировка внутри групп по одному ключу"""
        data = DictList2(
            [
                {"group": "A", "value": 3},
                {"group": "A", "value": 1},
                {"group": "B", "value": 2},
            ]
        )
        result = list(data.gen_filter(by="group", order="value"))
        group_a = [x for x in result if x[0]["group"] == "A"][0][1]
        assert [item["value"] for item in group_a] == [1, 3]

    def test_sort_within_group_by_multiple_keys(self):
        """Сортировка внутри групп по нескольким ключам"""
        data = DictList2(
            [
                {"g": 1, "a": 1, "b": 3},
                {"g": 1, "a": 1, "b": 1},
                {"g": 2, "a": 0, "b": 2},
            ]
        )
        result = list(data.gen_filter(by="g", order=["a", "b"]))
        group_1 = [x for x in result if x[0]["g"] == 1][0][1]
        assert [item["b"] for item in group_1] == [1, 3]

    def test_sort_with_order_dict(self):
        """Сортировка внутри групп по словарю ключей с направлением"""
        data = DictList2(
            [
                {"group": "X", "score": 2},
                {"group": "X", "score": 5},
                {"group": "X", "score": 1},
            ]
        )
        result = list(data.gen_filter(by="group", order={"score": "desc"}))
        values = [item["score"] for item in result[0][1]]
        assert values == [5, 2, 1]

    def test_empty_list(self):
        """Обработка пустого списка"""
        data = DictList2([])
        result = list(data.gen_filter(by="group"))
        assert result == []
