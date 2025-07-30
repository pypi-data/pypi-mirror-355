import logging  # noqa

from dictlist2 import DictList2


class TestDictList2GroupBy:
    """
    Тесты метода group_by() класса DictList2.

    Проверяемые случаи:
    -------------------
    1. Группировка по нескольким полям и суммирование числовых значений.
    2. Группировка по одному полю.
    3. Суммирование без группировки.
    4. Только группировка без суммирования.
    5. Пустой список данных.
    6. Отсутствие total_columns — только ключи группировки.
    7. Отсутствие group_columns — суммируются все.
    8. Отсутствие и group_columns, и total_columns — результат пустой.
    """

    def test_group_by_with_totals(self):
        """
        ✅ Суммирование по нескольким полям с группировкой по 2 ключам.
        """
        data = DictList2(
            [
                {"project": "A", "user": "Anna", "hours": 2, "cost": 100},
                {"project": "A", "user": "Anna", "hours": 1, "cost": 150},
                {"project": "A", "user": "Ivan", "hours": 3, "cost": 200},
                {"project": "B", "user": "Ivan", "hours": 4, "cost": 300},
            ]
        )
        result = data.group_by(
            group_columns=["project", "user"], total_columns=["hours", "cost"]
        )
        assert result == DictList2(
            [
                {"project": "A", "user": "Anna", "hours": 3, "cost": 250},
                {"project": "A", "user": "Ivan", "hours": 3, "cost": 200},
                {"project": "B", "user": "Ivan", "hours": 4, "cost": 300},
            ]
        )

    def test_group_by_single_column(self):
        """
        ✅ Группировка по одному полю и суммирование одного значения.
        """
        data = DictList2(
            [
                {"category": "X", "value": 10},
                {"category": "X", "value": 5},
                {"category": "Y", "value": 3},
            ]
        )
        result = data.group_by(group_columns="category", total_columns="value")
        assert result == DictList2(
            [
                {"category": "X", "value": 15},
                {"category": "Y", "value": 3},
            ]
        )

    def test_group_by_without_group_columns(self):
        """
        ✅ Только суммирование без группировки.
        """
        data = DictList2(
            [
                {"a": 1, "b": 2},
                {"a": 2, "b": 3},
            ]
        )
        result = data.group_by(group_columns=None, total_columns=["a", "b"])
        assert result == DictList2([{"a": 3, "b": 5}])

    def test_group_by_only_grouping(self):
        """
        ✅ Только группировка без total_columns.
        """
        data = DictList2(
            [
                {"a": 1, "b": 2},
                {"a": 1, "b": 2},
                {"a": 2, "b": 2},
            ]
        )
        result = data.group_by(group_columns=["a", "b"])
        assert result == DictList2(
            [
                {"a": 1, "b": 2},
                {"a": 2, "b": 2},
            ]
        )

    def test_group_by_empty_input(self):
        """
        ✅ Пустой список на входе — результат тоже пустой.
        """
        data = DictList2([])
        result = data.group_by(group_columns=["a"], total_columns=["x"])
        assert result == DictList2([])

    def test_group_by_no_total_columns(self):
        """
        ✅ Указаны только ключи группировки — значения не суммируются.
        """
        data = DictList2(
            [
                {"type": "A", "val": 5},
                {"type": "A", "val": 10},
                {"type": "B", "val": 3},
            ]
        )
        result = data.group_by(group_columns="type", total_columns=None)
        assert result == DictList2(
            [
                {"type": "A"},
                {"type": "B"},
            ]
        )

    def test_group_by_no_group_columns(self):
        """
        ✅ Нет ключей группировки — считается сумма по всем строкам.
        """
        data = DictList2(
            [
                {"val": 1},
                {"val": 4},
            ]
        )
        result = data.group_by(group_columns=None, total_columns="val")
        assert result == DictList2([{"val": 5}])

    def test_group_by_nothing(self):
        """
        ✅ Нет ни группировки, ни полей — результат пустой.
        """
        data = DictList2(
            [
                {"val": 1},
            ]
        )
        result = data.group_by(group_columns=None, total_columns=None)
        assert result == DictList2([])
