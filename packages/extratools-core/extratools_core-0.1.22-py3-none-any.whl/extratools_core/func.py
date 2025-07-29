from collections import Counter
from collections.abc import Callable, Iterable
from decimal import Decimal
from statistics import mean
from typing import Any, cast


# Name it in this way to mimic as a function
class lazy_call[T: Any]:  # noqa: N801
    __DEFAULT_OBJECT = object()

    def __init__(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

        self.__object: object | T = self.__DEFAULT_OBJECT

    def __call__(self) -> T:
        if self.__object == self.__DEFAULT_OBJECT:
            self.__object = self.__func(*self.__args, **self.__kwargs)

        return cast("T", self.__object)


# Name it in this way to mimic as a function
class multi_call[T: Any]:  # noqa: N801
    def __init__(
        self,
        times: int,
        agg_func: Callable[[Iterable[T]], T],
    ) -> None:
        self.__times = times
        self.__agg_func = agg_func

    def __call__(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        results = (
            func(*args, **kwargs)
            for i in range(self.__times)
        )

        return self.__agg_func(results)


# Name it in this way to mimic as a function
class multi_call_for_average[T: int | float | Decimal](multi_call[T]):  # noqa: N801
    def __init__(
        self,
        times: int,
    ) -> None:
        super().__init__(
            times,
            mean,
        )


# Name it in this way to mimic as a function
class multi_call_for_most_common[T: Any](multi_call[T]):  # noqa: N801
    def __init__(
        self,
        times: int,
    ) -> None:
        def most_commmon(results: Iterable[T]) -> T:
            return Counter(results).most_common(1)[0][0]

        super().__init__(
            times,
            most_commmon,
        )
