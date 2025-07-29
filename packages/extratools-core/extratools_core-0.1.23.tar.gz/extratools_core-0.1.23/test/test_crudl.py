from typing import Any

import pytest

from extratools_core.crudl import CRUDLDict, CRUDLWrapper, RLDict, RLWrapper
from extratools_core.test import is_proper_mapping, is_proper_mutable_mapping


def test_RLWrapper() -> None:  # noqa: N802
    wrapper = RLWrapper[str, int]({"Ada": 1, "Bob": 2}, values_in_list=True)

    assert wrapper.read("Ada") == 1
    assert list(wrapper.list()) == [("Ada", 1), ("Bob", 2)]
    assert list(wrapper.list(lambda key: key.startswith("B"))) == [("Bob", 2)]

    with pytest.raises(KeyError):
        wrapper.read("Chad")

    wrapper = CRUDLWrapper[str, int]({"Ada": 1, "Bob": 2})
    assert list(wrapper.list()) == [("Ada", None), ("Bob", None)]
    assert list(wrapper.list(lambda key: key.startswith("B"))) == [("Bob", None)]


def test_CRUDLWrapper() -> None:  # noqa: N802
    wrapper = CRUDLWrapper[str, int]({"Ada": 1, "Bob": 2}, values_in_list=True)

    assert wrapper.read("Ada") == 1
    assert list(wrapper.list()) == [("Ada", 1), ("Bob", 2)]
    assert list(wrapper.list(lambda key: key.startswith("B"))) == [("Bob", 2)]

    with pytest.raises(KeyError):
        wrapper.create("Bob", 2)

    assert wrapper.delete("Bob") == 2
    assert list(wrapper.list()) == [("Ada", 1)]

    with pytest.raises(KeyError):
        wrapper.read("Bob")

    wrapper.create("Bob", 2)
    assert wrapper.read("Bob") == 2
    assert list(wrapper.list()) == [("Ada", 1), ("Bob", 2)]

    with pytest.raises(KeyError):
        wrapper.delete("Chad")

    with pytest.raises(KeyError):
        wrapper.update("Chad", 3)

    wrapper.update("Bob", 3)
    assert wrapper.read("Bob") == 3
    assert list(wrapper.list()) == [("Ada", 1), ("Bob", 3)]

    wrapper = CRUDLWrapper[str, int]({"Ada": 1, "Bob": 2})
    assert list(wrapper.list()) == [("Ada", None), ("Bob", None)]
    assert list(wrapper.list(lambda key: key.startswith("B"))) == [("Bob", None)]


def test_RLDict() -> None:  # noqa: N802
    wrapper = CRUDLWrapper[str, int]({"Ada": 1, "Bob": 2})

    is_proper_mapping(
        lambda: RLDict(
            read_func=wrapper.read,
            list_func=wrapper.list,
        ),
        key_cls=lambda: "Chad",
        value_cls=lambda: 3,
    )


def test_CRUDLDict() -> None:  # noqa: N802
    wrapper = CRUDLWrapper[str, int]({"Ada": 1, "Bob": 2})

    def create(key: str | None, value: Any) -> int:
        if key is None:
            raise KeyError

        return wrapper.create(key, value)

    is_proper_mutable_mapping(
        lambda: CRUDLDict(
            create_func=create,
            read_func=wrapper.read,
            update_func=wrapper.update,
            delete_func=wrapper.delete,
            list_func=wrapper.list,
        ),
        key_cls=lambda: "Chad",
        value_cls=lambda: 3,
    )
