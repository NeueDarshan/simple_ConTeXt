import random


def safe_random_sample(data, size):
    if size < len(data):
        return random.sample(data, size)
    return data


def poly_biased_random_sample(min_, max_, size, power=2):
    if size < max_ - min_:
        sample = []
        while len(sample) < size:
            x = pow(random.random(), power)
            n = min_ + round((max_ - min_) * x)
            if n not in sample:
                sample.append(n)
        return sample
    return range(min_, max_ + 1)


def poly_biased_randint(min_, max_, power=2, ignore=[]):
    while True:
        x = pow(random.random(), power)
        n = min_ + round((max_ - min_) * x)
        if n not in ignore:
            return n
