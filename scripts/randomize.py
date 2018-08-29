import random

from typing import Container, Optional, Sequence, TypeVar


T = TypeVar("T")


def safe_random_sample(data: Sequence[T], size: int) -> Sequence[T]:
    if size < len(data):
        return random.sample(data, size)
    return data


def poly_biased_randint(
    min_: int,
    max_: int,
    power: int = 2,
    ignore: Optional[Container[int]] = None,
) -> int:
    ignore = [] if ignore is None else ignore
    while True:
        x = pow(random.random(), power)
        n = min_ + round((max_ - min_) * x)
        if n not in ignore:
            return n
