import logging  # noqa
import pytest

from dictlist2 import DictList2


class TestDictList2Aggregate:
    """
    Тесты метода aggregate() класса DictList2.

    Описания сценариев:
    -------------------
    1. Агрегация с группировкой по одному полю.
    2. Несколько агрегаций по разным полям.
    3. Агрегация без группировки (вся выборка как одна группа).
    4. Проверка поведения при пустом списке.
    5. Проверка обработки несуществующего поля.
    6. Проверка ошибки при неправильном типе агрегации.
    """

    def test_aggregate_with_group_by(self):
        """
        ✅ Группировка по одному полю, агрегации: sum, avg, min, max, count.
        """
        data = DictList2(
            [
                {"project": "A", "hours": 5},
                {"project": "A", "hours": 3},
                {"project": "B", "hours": 8},
            ]
        )
        result = data.aggregate(
            group_columns="project",
            aggregations={
                "hours": ["sum", "avg", "min", "max"],
                "project": "count",
            },
        )
        assert result == [
            {
                "project": "A",
                "hours_sum": 8,
                "hours_avg": 4.0,
                "hours_min": 3,
                "hours_max": 5,
                "project_count": 2,
            },
            {
                "project": "B",
                "hours_sum": 8,
                "hours_avg": 8.0,
                "hours_min": 8,
                "hours_max": 8,
                "project_count": 1,
            },
        ]

    def test_aggregate_multiple_fields(self):
        """
        ✅ Агрегация по нескольким полям и разным операциям.
        """
        data = DictList2(
            [
                {"category": "X", "views": 10, "likes": 2},
                {"category": "X", "views": 5, "likes": 3},
                {"category": "Y", "views": 8, "likes": 1},
            ]
        )
        result = data.aggregate(
            group_columns="category",
            aggregations={"views": "sum", "likes": ["sum", "max"]},
        )
        assert result == [
            {"category": "X", "views_sum": 15, "likes_sum": 5, "likes_max": 3},
            {"category": "Y", "views_sum": 8, "likes_sum": 1, "likes_max": 1},
        ]

    def test_aggregate_no_grouping(self):
        """
        ✅ Агрегация всей выборки как одной группы.
        """
        data = DictList2(
            [
                {"val": 2},
                {"val": 4},
                {"val": 9},
            ]
        )
        result = data.aggregate(
            group_columns=None,
            aggregations={"val": ["sum", "avg", "min", "max"]},
        )
        assert result == [
            {"val_sum": 15, "val_avg": 5.0, "val_min": 2, "val_max": 9}
        ]

    def test_aggregate_empty_list(self):
        """
        ✅ Пустой список — возвращается пустой результат.
        """
        data = DictList2([])
        result = data.aggregate(
            group_columns="any", aggregations={"val": "sum"}
        )
        assert result == []

    def test_aggregate_missing_field(self):
        """
        ✅ Если поле отсутствует — считается 0.
        """
        data = DictList2(
            [
                {"name": "A"},
                {"name": "B"},
            ]
        )
        result = data.aggregate(
            group_columns="name", aggregations={"score": "sum"}
        )
        assert result == [
            {"name": "A", "score_sum": 0},
            {"name": "B", "score_sum": 0},
        ]

    def test_aggregate_invalid_aggregation(self):
        """
        ❌ Ошибка при передаче неизвестного типа агрегации.
        """
        data = DictList2(
            [
                {"x": 1},
                {"x": 2},
            ]
        )
        with pytest.raises(ValueError, match="Unknown aggregation type"):
            data.aggregate(group_columns="x", aggregations={"x": "median"})


class TestDictList2AggregateExtended:
    """
    Расширенные тесты метода aggregate() класса DictList2.

    Дополнительные сценарии:
    -------------------------
    7. Обработка значений None при агрегации.
    8. Агрегация по строковым полям (только count имеет смысл).
    9. Отсутствие поля в одном из элементов.
    10. Отсутствие агрегаций — должен возвращаться пустой результат.
    """

    def test_aggregate_with_none_values(self):
        """
        ✅ Значения None игнорируются или считаются как 0.
        """
        data = DictList2(
            [
                {"group": "A", "score": 10},
                {"group": "A", "score": None},
                {"group": "B", "score": 5},
                {"group": "B"},
            ]
        )
        result = data.aggregate(
            group_columns="group",
            aggregations={"score": ["sum", "avg", "min", "max"]},
        )
        assert result == [
            {
                "group": "A",
                "score_sum": 10,
                "score_avg": 5.0,
                "score_min": 0,
                "score_max": 10,
            },
            {
                "group": "B",
                "score_sum": 5,
                "score_avg": 2.5,
                "score_min": 0,
                "score_max": 5,
            },
        ]

    def test_aggregate_on_strings_with_count(self):
        """
        ✅ Агрегация count работает для строк.
        """
        data = DictList2(
            [
                {"type": "A"},
                {"type": "A"},
                {"type": "B"},
            ]
        )
        result = data.aggregate(
            group_columns="type", aggregations={"type": "count"}
        )
        assert result == [
            {"type": "A", "type_count": 2},
            {"type": "B", "type_count": 1},
        ]

    def test_aggregate_missing_field_in_some_items(self):
        """
        ✅ Отсутствующее поле считается как 0.
        """
        data = DictList2(
            [
                {"group": "X", "value": 4},
                {"group": "X"},  # нет поля 'value'
            ]
        )
        result = data.aggregate(
            group_columns="group", aggregations={"value": ["sum", "max"]}
        )
        assert result == [{"group": "X", "value_sum": 4, "value_max": 4}]

    def test_aggregate_no_aggregations(self):
        """
        ✅ Если агрегации не указаны, возвращается пустой словарь в группе.
        """
        data = DictList2(
            [
                {"type": "A", "val": 10},
                {"type": "A", "val": 5},
            ]
        )
        result = data.aggregate(group_columns="type", aggregations={})
        assert result == [{"type": "A"}]

    def test_aggregate_with_mixed_data_types(self):
        """
        ✅ Строки и числа в одном поле — исключение не возникает.
        """
        data = DictList2(
            [
                {"category": "A", "value": 10},
                {"category": "A", "value": "not a number"},
            ]
        )
        # Неверные типы игнорируются, будет ошибка при попытке агрегации
        with pytest.raises(TypeError):
            data.aggregate(
                group_columns="category", aggregations={"value": "sum"}
            )
