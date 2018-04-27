import random


def safe_random_sample(data, size):
    if size < len(data):
        return random.sample(data, size)
    return data


def poly_biased_randint(min_, max_, power=2, ignore=None):
    ignore = [] if ignore is None else ignore
    while True:
        x = pow(random.random(), power)
        n = min_ + round((max_ - min_) * x)
        if n not in ignore:
            return n
