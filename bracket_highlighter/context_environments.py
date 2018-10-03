import re


def agree(one, two):
    return one and two and one.group(1) == two.group(1)


def compare(name, first, second, bfr):
    one, two = bfr[first.begin:first.end], bfr[second.begin:second.end]
    start_one = re.match(r"\\start([a-zA-Z]*)", one)
    start_two = re.match(r"\\stop([a-zA-Z]*)", two)
    if agree(start_one, start_two):
        return True
    begin_one = re.match(r"\\bT([A-Z]+[a-zA-Z]*)", one)
    begin_two = re.match(r"\\eT([A-Z]+[a-zA-Z]*)", two)
    if agree(begin_two, begin_one):
        return True
    return False
