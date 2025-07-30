import logging  # noqa
from typing import Union, List, Any, Dict, Iterator, Tuple, Self
from functools import reduce


class DictList2(list):
    """
    Расширенный список для работы с массивами словарей.

    Предоставляет методы для удобной обработки коллекций словарей:
    - unique(): исключает дубликаты;
    - sort(): сортирует по одному или нескольким ключам;
    - distinct(): возвращает уникальные значения по заданным ключам;
    - filter(): фильтрует по значению одного или нескольких полей;
    - gen_filter(): группирует и возвращает генератор (группа → элементы);
    - join(): внутреннее объединение по ключу;
    - left_join(): левое объединение по ключу;
    - group_by(): группировка с суммированием полей;
    - aggregate(): универсальная агрегация (sum, count, avg, min, max).

    Подходит для подготовки отчётов, аналитики, группировки данных и
    построения таблиц без сторонних библиотек.

    Все методы возвращают новые списки, не модифицируя оригинальные данные.
    """

    def unique(self) -> Self:
        """
        Возвращает список уникальных словарей на основе всех ключей и значений.

        data = DictList2([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 1, "name": "Alice"},  # дубликат
            {"id": 3, "name": "Charlie"},
            {"name": "Bob", "id": 2}, # считается дубликатом
            (ключи и значения те же)
        ])

        result = data.unique()

        {'id': 1, 'name': 'Alice'}
        {'id': 2, 'name': 'Bob'}
        {'id': 3, 'name': 'Charlie'}

        :return: Список уникальных словарей без дубликатов
        """
        seen = set()
        result = []

        for item in self:
            # Преобразуем словарь в кортеж пар (ключ, значение) -
            # хэшируемое представление
            key = frozenset(item.items())
            if key not in seen:
                seen.add(key)
                result.append(item)

        return DictList2(result)

    def sort(
        self, by: Union[str, List[str]] = None, reverse: bool = False
    ) -> Self:
        """
        Сортировка списка словарей по одному или нескольким ключам.

        # Пример 1: Сортировка по одному полю

        data = DictList2([
            {"id": 3, "name": "Charlie"},
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])

        sorted_data = data.sort(by="id")

        {'id': 1, 'name': 'Alice'}
        {'id': 2, 'name': 'Bob'}
        {'id': 3, 'name': 'Charlie'}

        # Пример 2: Сортировка по нескольким ключам

        data = DictList2([
            {"city": "Moscow", "age": 30},
            {"city": "Moscow", "age": 25},
            {"city": "London", "age": 40},
        ])

        sorted_data = data.sort(by=["city", "age"])

        {'city': 'London', 'age': 40}
        {'city': 'Moscow', 'age': 25}
        {'city': 'Moscow', 'age': 30}

        :param by: ключ (str) или список ключей (list[str]) для сортировки
        :param reverse: если True — сортировка в обратном порядке
        :return: отсортированный список словарей
        """
        if by is None:
            return self

        if isinstance(by, list):
            return DictList2(
                sorted(
                    self,
                    key=lambda item: tuple(item[key] for key in by),
                    reverse=reverse,
                )
            )

        return DictList2(
            sorted(self, key=lambda item: item[by], reverse=reverse)
        )

    def distinct(self, by: Union[str, List[str], None] = None) -> Self:
        """
        Возвращает уникальные элементы из списка словарей.

        Если параметр `by` не указан, уникальность определяется по всем ключам
        и значениям словаря.
        Если `by` задан, возвращаются только указанные поля
        с уникальными сочетаниями значений.

        :param by: Ключ или список ключей, по которым нужно определить
                уникальность.
        :return: Список словарей с уникальными значениями.

        Примеры:
        --------
        Уникальность по всем полям:

        >>> data = DictList2([
        ...     {"id": 1, "name": "Alice"},
        ...     {"id": 1, "name": "Alice"},
        ...     {"id": 2, "name": "Bob"},
        ... ])
        >>> data.distinct()
        [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]

        Уникальность по одному полю:

        >>> data.distinct(by="name")
        [{'name': 'Alice'}, {'name': 'Bob'}]

        Уникальность по нескольким полям:

        >>> data = DictList2([
        ...     {"id": 1, "project": "A", "name": "Anna"},
        ...     {"id": 2, "project": "A", "name": "Anna"},
        ...     {"id": 3, "project": "B", "name": "Anna"},
        ... ])
        >>> data.distinct(by=["project", "name"])
        [{'project': 'A', 'name': 'Anna'}, {'project': 'B', 'name': 'Anna'}]
        """
        if by is None:
            # Уникальность по всему словарю
            seen = set()
            result = []
            for item in self:
                key = frozenset(item.items())
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            return DictList2(result)

        # Уникальность только по указанным полям
        keys = [by] if isinstance(by, str) else by
        seen = set()
        result = []
        for item in self:
            key = tuple(item.get(k) for k in keys)
            if key not in seen:
                seen.add(key)
                result.append({k: item.get(k) for k in keys})

        # Сортировка по тем же полям
        return DictList2(
            sorted(
                result,
                key=lambda row: tuple(
                    row[k] if row[k] is not None else "" for k in keys
                ),
            )
        )

    def filter(
        self, where: Dict[str, Any], order: Union[str, List[str], None] = None
    ) -> Self:
        """
        Возвращает отфильтрованный список словарей по заданным условиям.

        Сравнение выполняется по точному совпадению значений ключей. Также
        можно указать сортировку результата по одному или нескольким полям.

        :param where: Условия фильтрации в виде словаря {ключ: значение}.
        :param order: Ключ или список ключей для сортировки результата.
        :return: Отфильтрованный и (опционально) отсортированный список.

        Примеры:
        --------
        >>> data = DictList2([
        ...     {"id": 1, "name": "Alice", "role": "Admin"},
        ...     {"id": 2, "name": "Bob", "role": "User"},
        ...     {"id": 3, "name": "Alice", "role": "User"},
        ... ])

        Фильтрация по имени:

        >>> data.filter(where={"name": "Alice"})
        [{'id': 1, 'name': 'Alice', 'role': 'Admin'},
         {'id': 3, 'name': 'Alice', 'role': 'User'}]

        Фильтрация и сортировка по id:

        >>> data.filter(where={"role": "User"}, order="id")
        [{'id': 2, 'name': 'Bob', 'role': 'User'},
         {'id': 3, 'name': 'Alice', 'role': 'User'}]
        """

        def matches(item: Dict[str, Any]) -> bool:
            return all(item.get(k) == v for k, v in where.items())

        filtered = [item for item in self if matches(item)]

        if order:
            return DictList2(filtered).sort(by=order)
        return DictList2(filtered)

    def gen_filter(
        self,
        by: Union[str, List[str], None],
        order: Union[str, List[str], Dict[str, str], None] = None,
    ) -> Iterator[Tuple[Dict[str, Any], Self]]:
        """
        Генератор: группирует элементы по уникальным значениям `by` и
        возвращает пары (значения группы, элементы группы). Если указан
        параметр `order`, элементы внутри группы будут отсортированы.

        :param by: Ключ или список ключей, по которым группировать.
        :param order: Ключ, список ключей или словарь {ключ: 'asc'|'desc'}
                    для сортировки в каждой группе.
        :yield: Кортеж (значения группы, список элементов в группе).

        Примеры:
        --------
        >>> data = DictList2([
        ...     {"project": "A", "user": "Anna", "hours": 2},
        ...     {"project": "A", "user": "Ivan", "hours": 3},
        ...     {"project": "B", "user": "Anna", "hours": 4},
        ...     {"project": "A", "user": "Anna", "hours": 1},
        ... ])

        >>> for key, group in data.gen_filter(
        ...     by=["project", "user"], order={"hours": "desc"}):
        ...     print(key)
        ...     for row in group:
        ...         print("  ", row)
        """
        for group_key in self.distinct(by=by):

            def matches(item: Dict[str, Any]) -> bool:
                return all(item.get(k) == v for k, v in group_key.items())

            group_items = [item for item in self if matches(item)]

            if isinstance(order, dict):
                # Сортировка по каждому полю с направлением
                keys = list(order.keys())
                reverse_flags = [order[k] == "desc" for k in keys]

                def sort_key(item):
                    return tuple(item.get(k) for k in keys)

                group_items.sort(
                    key=sort_key,
                    reverse=(
                        all(reverse_flags)
                        if len(set(reverse_flags)) == 1
                        else False
                    ),
                )

            elif order:
                group_items = DictList2(group_items).sort(by=order)

            yield group_key, DictList2(group_items)

    def join(self, right: Self, key: str) -> Self:
        """
        Выполняет внутреннее объединение (inner join) текущего списка
        с другим по заданному ключу.

        # Левый список (основной)
        left = DictList2([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ])

        # Правый список (дополняющий)
        right = [
            {"id": 1, "role": "Admin"},
            {"id": 2, "role": "User"},
            {"id": 4, "role": "Guest"},
        ]

        # Inner join по ключу "id"
        joined = left.join(right, key="id")

        {'id': 1, 'name': 'Alice', 'role': 'Admin'}
        {'id': 2, 'name': 'Bob', 'role': 'User'}

        :param dict_list: список словарей, с которым нужно объединить
        :param key: ключ, по которому происходит объединение
        :return: список словарей, где ключ есть в обоих списках
        """
        # Индекс правого списка по ключу
        right_index = {item[key]: item for item in right}

        # Объединяем только те элементы, у которых ключ есть в обоих списках
        result = []
        for item in self:
            match = right_index.get(item.get(key))
            if match:
                result.append({**item, **match})
        return DictList2(result)

    def left_join(self, right: List[Dict[str, Any]], key: str) -> Self:
        """
        Выполняет левое объединение (left join) текущего списка словарей
        с другим по указанному ключу.

        # Пример левого списка (основа)
        left = DictList2([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ])

        # Пример правого списка (дополняем по id)
        right = [
            {"id": 1, "role": "Admin"},
            {"id": 2, "role": "User"},
            {"id": 4, "role": "Guest"},
        ]

        # Выполняем left join
        result = left.left_join(right, key="id")

        {'id': 1, 'name': 'Alice', 'role': 'Admin'}
        {'id': 2, 'name': 'Bob', 'role': 'User'}
        {'id': 3, 'name': 'Charlie'}

        :param right: внешний список (тот, из которого дополняются поля)
        :param key: имя ключа, по которому происходит объединение
        :return: новый список словарей с объединёнными значениями
        """
        # Индекс правой таблицы по ключу
        right_index = {item[key]: item for item in right}

        result = []
        for left_item in self:
            merged = dict(left_item)  # копируем левый элемент
            right_item = right_index.get(left_item.get(key))
            if right_item:
                # добавляем недостающие поля из правого
                for k, v in right_item.items():
                    if k not in merged:
                        merged[k] = v
            result.append(merged)

        return DictList2(result)

    def group_by(
        self,
        group_columns: Union[str, List[str], None] = None,
        total_columns: Union[str, List[str], None] = None,
    ) -> Self:
        """
        Сгруппировать список словарей по указанным полям и просуммировать
        числовые значения.

        data = DictList2([
            {"project": "A", "user": "Anna", "hours": 2, "cost": 100},
            {"project": "A", "user": "Anna", "hours": 1, "cost": 150},
            {"project": "A", "user": "Ivan", "hours": 3, "cost": 200},
            {"project": "B", "user": "Ivan", "hours": 4, "cost": 300},
        ])

        result = data.group_by(
            group_columns=["project", "user"],
            total_columns=["hours", "cost"]
        )
        print(result)
        # 👉 [
        #   {'project': 'A', 'user': 'Anna', 'hours': 3, 'cost': 250},
        #   {'project': 'A', 'user': 'Ivan', 'hours': 3, 'cost': 200},
        #   {'project': 'B', 'user': 'Ivan', 'hours': 4, 'cost': 300},
        # ]

        :param group_columns: поле или список полей для группировки.
            Если None — без группировки.
        :param total_columns: поле или список полей для суммирования.
            Если None — только группировка.
        :return: список словарей с результатами группировки и суммирования
        """
        group_keys = (
            [group_columns]
            if isinstance(group_columns, str)
            else group_columns
        )
        sum_fields = (
            [total_columns]
            if isinstance(total_columns, str)
            else total_columns
        )

        # Если нет группировки — просто считаем сумму по всему списку
        if not group_keys:
            if not sum_fields:
                return DictList2([])

            total = {field: 0 for field in sum_fields}
            for item in self:
                for field in sum_fields:
                    total[field] += item.get(field, 0)
            return DictList2([total])

        # Группировка по полям
        result = []
        unique_groups = DictList2(self).distinct(group_keys)

        for group in unique_groups:
            group_data = DictList2(self).filter(group)
            group_total = {}

            if sum_fields:
                group_total = {field: 0 for field in sum_fields}
                for item in group_data:
                    for field in sum_fields:
                        group_total[field] += item.get(field, 0)

            result.append({**group, **group_total})

        return DictList2(result)

    def aggregate(
        self,
        group_columns: Union[str, List[str], None] = None,
        aggregations: Dict[str, Union[str, List[str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Универсальная группировка с поддержкой агрегаций:
        sum, count, avg, min, max.

        data = DictList2([
            {"project": "A", "hours": 5},
            {"project": "A", "hours": 3},
            {"project": "B", "hours": 8},
        ])

        result = data.aggregate(
            group_columns="project",
            aggregations={"hours": ["sum", "avg", "min", "max"],
                "project": "count"}
        )

        [
            {'project': 'A', 'hours_sum': 8, 'hours_avg': 4.0, 'hours_min': 3,
                'hours_max': 5, 'project_count': 2},
            {'project': 'B', 'hours_sum': 8, 'hours_avg': 8.0, 'hours_min': 8,
                'hours_max': 8, 'project_count': 1}
        ]

        :param group_columns: Ключ или список ключей для группировки.
            Если None — все данные считаются одной группой.
        :param aggregations: Словарь вида {'hours': 'sum', 'id': 'count'}
            или {'hours': ['sum', 'avg']}
        :return: Список сгруппированных словарей с результатами агрегаций
        """
        group_keys = (
            [group_columns]
            if isinstance(group_columns, str)
            else group_columns
        )
        aggregations = aggregations or {}

        # Универсальные агрегаторы
        def apply_aggregation(items: List[dict], field: str, agg: str) -> Any:
            values = [item.get(field, 0) for item in items]

            def zero(value):
                return 0 if value is None else value

            if agg == "sum":
                # return sum(values)
                return reduce(lambda acc, x: acc + zero(x), values)
            elif agg == "count":
                return len(items)
            elif agg == "avg":
                return (
                    reduce(lambda acc, x: acc + zero(x), values) / len(values)
                    if values
                    else 0
                )
            elif agg == "min":
                return (
                    reduce(
                        lambda a, b: zero(a) if zero(a) < zero(b) else zero(b),
                        values,
                    )
                    if values
                    else 0
                )
            elif agg == "max":
                return (
                    reduce(
                        lambda a, b: zero(a) if zero(a) > zero(b) else zero(b),
                        values,
                    )
                    if values
                    else 0
                )
            else:
                raise ValueError(f"Unknown aggregation type: {agg}")

        if group_keys is None:
            # Всё как одна группа
            group_data = list(self)
            result = {}
            for field, ops in aggregations.items():
                ops_list = [ops] if isinstance(ops, str) else ops
                for op in ops_list:
                    key = (
                        f"{field}_{op}" if op != "count" else f"{field}_count"
                    )
                    result[key] = apply_aggregation(group_data, field, op)
            return DictList2([result])

        # Группировка по ключам
        unique_groups = DictList2(self).distinct(group_keys)
        results = []

        for group_filter in unique_groups:
            group_data = DictList2(self).filter(group_filter)
            aggregated = {}

            for field, ops in aggregations.items():
                ops_list = [ops] if isinstance(ops, str) else ops
                for op in ops_list:
                    key = (
                        f"{field}_{op}" if op != "count" else f"{field}_count"
                    )
                    aggregated[key] = apply_aggregation(group_data, field, op)

            results.append({**group_filter, **aggregated})

        return DictList2(results)
