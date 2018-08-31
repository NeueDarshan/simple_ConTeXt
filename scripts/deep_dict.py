"""
Unfortunately, the `typing` module in python at time of writing is
insufficiently expressive to describe the functions in *this* module. We need
the following to all work together: parametric polymorphism, recursive types,
and sum types.

In lieu of such, we do what we can and fall back on `Any` where necessary.
"""


from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar


K = TypeVar("K")
V = TypeVar("V")


def update(dict_: Dict[K, Any], new_dict: Dict[K, Any]) -> None:
    for k, v in new_dict.items():
        if isinstance(v, dict):
            if k not in dict_:
                dict_[k] = {}
            update(dict_[k], v)
        else:
            dict_[k] = v


def iter_(dict_: Dict[K, Any]) -> Iterable[Tuple[List[K], Any]]:
    for k, v in dict_.items():
        if isinstance(v, dict):
            for key, val in iter_(v):
                yield [k] + key, val
        else:
            yield [k], v


def get(dict_: Dict[K, Any], keys: List[K]) -> Any:
    if not keys:
        return dict_
    elif len(keys) == 1:
        return dict_[keys[0]]
    return get(dict_[keys[0]], keys[1:])


def get_safe(dict_: Dict[K, Any], keys: List[K]) -> Any:
    if not keys:
        return dict_
    elif len(keys) == 1:
        return dict_.get(keys[0])
    dict_.setdefault(keys[0], {})
    return get_safe(dict_[keys[0]], keys[1:])


def set_(dict_: Dict[K, Any], keys: List[K], value: Any) -> None:
    if len(keys) <= 1:
        dict_[keys[0]] = value
    else:
        set_(dict_[keys[0]], keys[1:], value)


def set_safe(dict_: Dict[K, Any], keys: List[K], value: Any) -> None:
    if len(keys) <= 1:
        dict_[keys[0]] = value
    else:
        dict_.setdefault(keys[0], {})
        set_safe(dict_[keys[0]], keys[1:], value)


def in_(dict_: Dict[K, Any], keys: List[K]) -> bool:
    if len(keys) <= 1:
        return keys[0] in dict_
    return in_(dict_[keys[0]], keys[1:])


def del_(dict_: Dict[K, Any], keys: List[K]) -> None:
    if len(keys) <= 1:
        del dict_[keys[0]]
    else:
        del_(dict_[keys[0]], keys[1:])


def del_safe(dict_: Dict[K, Any], keys: List[K]) -> None:
    if len(keys) <= 1:
        try:
            del dict_[keys[0]]
        except KeyError:
            pass
    else:
        dict_.setdefault(keys[0], {})
        del_safe(dict_[keys[0]], keys[1:])
