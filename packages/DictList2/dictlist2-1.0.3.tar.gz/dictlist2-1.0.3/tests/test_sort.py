import logging  # noqa
import pytest

from dictlist2 import DictList2


def test_sort_single_key_ascending():
    """
    Проверяет сортировку по одному ключу по возрастанию.
    """
    data = DictList2(
        [
            {"id": 3, "name": "Charlie"},
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
    )

    result = data.sort(by="id")

    assert result == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
    ]


def test_sort_single_key_descending():
    """
    Проверяет сортировку по одному ключу по убыванию.
    """
    data = DictList2(
        [
            {"id": 1},
            {"id": 3},
            {"id": 2},
        ]
    )
    result = data.sort(by="id", reverse=True)
    assert result == [{"id": 3}, {"id": 2}, {"id": 1}]


def test_sort_multiple_keys():
    """
    Проверяет сортировку по нескольким ключам (вложенный порядок).
    """
    data = DictList2(
        [
            {"city": "Moscow", "age": 30},
            {"city": "Moscow", "age": 25},
            {"city": "London", "age": 40},
        ]
    )

    result = data.sort(by=["city", "age"])

    assert result == [
        {"city": "London", "age": 40},
        {"city": "Moscow", "age": 25},
        {"city": "Moscow", "age": 30},
    ]


def test_sort_with_none_key_argument():
    """
    Проверяет, что при отсутствии ключа сортировки возвращается оригинал.
    """
    data = DictList2(
        [
            {"id": 2},
            {"id": 1},
        ]
    )

    result = data.sort(by=None)

    assert result == data  # порядок не изменился


def test_sort_on_missing_key_raises():
    """
    Проверяет, что при отсутствии ключа в элементе словаря возникает KeyError.
    """
    data = DictList2(
        [
            {"id": 1},
            {"name": "Alice"},
        ]
    )

    with pytest.raises(KeyError):
        data.sort(by="id")


def test_sort_preserves_original_type():
    """
    Проверяет, что результат сортировки остаётся экземпляром DictList2.
    """
    data = DictList2(
        [
            {"id": 2},
            {"id": 1},
        ]
    )

    result = data.sort(by="id")
    assert isinstance(result, DictList2)
