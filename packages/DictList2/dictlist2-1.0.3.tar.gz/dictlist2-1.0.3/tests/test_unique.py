import logging  # noqa
import pytest

from dictlist2 import DictList2


def test_unique_removes_duplicates():
    """
    Дубликаты с одинаковыми ключами и значениями исключаются;
    Порядок ключей в словарях не влияет на уникальность;
    Возвращается корректный список уникальных словарей.
    """
    data = DictList2(
        [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 1, "name": "Alice"},  # дубликат
            {"id": 3, "name": "Charlie"},
            {"name": "Bob", "id": 2},  # дубликат с другим порядком ключей
        ]
    )

    result = data.unique()

    expected = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
    ]

    # Сравниваем, игнорируя порядок ключей
    assert len(result) == len(expected)
    for item in expected:
        assert item in result


def test_unique_empty_list():
    """
    проверка поведения при пустом списке.
    """
    data = DictList2([])
    result = data.unique()
    assert result == []


def test_unique_all_unique():
    """
    если все словари уникальны, они должны остаться.
    """
    data = DictList2(
        [
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]
    )
    result = data.unique()
    assert result == data


def test_unique_nested_dicts_are_not_removed():
    """
    демонстрирует ограничение:
    метод .unique() не поддерживает словари с вложенными словарями
    из-за TypeError при попытке сделать frozenset(dict.items()).
    """
    data = DictList2(
        [
            {"id": 1, "meta": {"a": 1}},  # вложенный словарь
            {"id": 1, "meta": {"a": 1}},  # дубликат
        ]
    )

    # Поскольку frozenset(item.items()) не работает для вложенных словарей,
    # ожидается исключение TypeError
    with pytest.raises(TypeError):
        _ = data.unique()
