from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping
from typing import Any, cast


class RLWrapper[KT: Any, VT: Any]:
    def __init__(
        self,
        mapping: Mapping[KT, VT],
        *,
        values_in_list: bool = False,
    ) -> None:
        self.mapping = mapping

        self.__values_in_list = values_in_list

    def read(self, key: KT) -> VT:
        return self.mapping[key]

    def list(
        self,
        filter_func: Callable[[KT], bool] | None = None,
    ) -> Iterable[tuple[KT, VT | None]]:
        if filter_func is None:
            if self.__values_in_list:
                yield from self.mapping.items()
            else:
                for key in self.mapping:
                    yield key, None
        else:
            for key in filter(filter_func, self.mapping):
                yield key, self.mapping[key] if self.__values_in_list else None


class CRUDLWrapper[KT: Any, VT: Any](RLWrapper[KT, VT]):
    def __init__(
        self,
        mapping: MutableMapping[KT, VT],
        *,
        values_in_list: bool = False,
    ) -> None:
        super().__init__(
            mapping,
            values_in_list=values_in_list,
        )

        self.mapping = mapping

    def create(self, key: KT, value: VT) -> VT:
        if key in self.mapping:
            raise KeyError

        self.mapping[key] = value
        return value

    def update(self, key: KT, value: VT) -> VT:
        if key not in self.mapping:
            raise KeyError

        self.mapping[key] = value
        return value

    def delete(self, key: KT) -> VT:
        default = object()
        value = self.mapping.pop(key, default)
        if value == default:
            raise KeyError

        return cast("VT", value)


class RLDict[KT: Any, VT: Any](Mapping[KT, VT]):
    def __init__(
        self,
        *,
        read_func: Callable[[KT], VT],
        list_func: Callable[[Any | None], Iterable[tuple[KT, VT | None]]],
    ) -> None:
        self.__read_func = read_func
        self.__list_func = list_func

    def __getitem__(self, key: KT) -> VT:
        return self.__read_func(key)

    def __iter__(self) -> Iterator[KT]:
        for key, _ in self.__list_func(None):
            yield key

    def __len__(self) -> int:
        # Cannot use `count` in `toolz` as itself depends on this function
        count = 0
        for _ in self:
            count += 1
        return count


class CRUDLDict[KT: Any, VT: Any](MutableMapping[KT, VT], RLDict[KT, VT]):
    def __init__(
        self,
        *,
        create_func: Callable[[KT | None, Any], VT | None],
        read_func: Callable[[KT], VT],
        update_func: Callable[[KT, Any], VT | None],
        delete_func: Callable[[KT], VT | None],
        list_func: Callable[[Any | None], Iterable[tuple[KT, VT | None]]],
    ) -> None:
        RLDict.__init__(
            self,
            read_func=read_func,
            list_func=list_func,
        )

        self.__create_func = create_func
        self.__read_func = read_func
        self.__update_func = update_func
        self.__delete_func = delete_func
        self.__list_func = list_func

    def __delitem__(self, key: KT) -> None:
        self.__delete_func(key)

    def __setitem__(self, key: KT | None, value: VT) -> None:
        if key is None or key not in self:
            self.__create_func(key, value)
        else:
            self.__update_func(key, value)
