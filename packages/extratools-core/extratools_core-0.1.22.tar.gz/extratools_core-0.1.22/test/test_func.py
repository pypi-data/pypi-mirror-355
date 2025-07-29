from collections import Counter
from random import randint
from statistics import mean

from extratools_core.func import lazy_call, multi_call_for_average, multi_call_for_most_common


def test_lazy_call_func() -> None:
    count = 0

    def f(name: str) -> str:
        nonlocal count
        count += 1

        return f"{name}_{count}"

    lc1 = lazy_call(f, "Ada")
    assert lc1() == "Ada_1"
    lc2 = lazy_call(f, "Bob")
    assert lc2() == "Bob_2"
    assert lc1() == "Ada_1"
    assert lc2() == "Bob_2"


def test_lazy_call_class() -> None:
    class C:
        count = 0

        def __init__(self, name: str) -> None:
            C.count += 1

            self.__name = f"{name}_{C.count}"

        def name(self) -> str:
            return self.__name

    lc1 = lazy_call(C, "Ada")
    assert lc1().name() == "Ada_1"
    lc2 = lazy_call(C, "Bob")
    assert lc2().name() == "Bob_2"
    assert lc1().name() == "Ada_1"
    assert lc2().name() == "Bob_2"


def test_multi_call_by_average() -> None:
    values = []

    def f(i: int) -> int:
        v = randint(0, i)
        values.append(v)
        return v

    mc1 = multi_call_for_average(3)
    assert len(values) == 0
    agg_value = mc1(f, 10)
    assert len(values) == 3
    assert mean(values) == agg_value


def test_multi_call_by_most_common() -> None:
    values = []

    def f(i: int) -> int:
        v = randint(0, i)
        values.append(v)
        return v

    mc1 = multi_call_for_most_common(10)
    assert len(values) == 0
    agg_value = mc1(f, 3)
    assert len(values) == 10
    assert Counter(values).most_common(1)[0][0] == agg_value
