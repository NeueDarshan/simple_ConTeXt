import re


def compare(name, first, second, bfr):
    one = re.match(r"\\start([a-zA-Z]*)", bfr[first.begin:first.end])
    two = re.match(r"\\stop([a-zA-Z]*)", bfr[second.begin:second.end])
    return one and two and one.group(1) == two.group(1)
