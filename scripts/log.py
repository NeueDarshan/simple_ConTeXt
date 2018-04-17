import re

# from . import utilities


def translate_class(text):
    if text == "mp":
        return "metapost"
    return text


def parse(data, code):
    result = ""
    success = code == 0
    text = data.decode(encoding="utf-8", errors="ignore")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if success:
        result += "  - finished successfully\n"
    else:
        result += "  - finished unsuccessfully\n"

    temp = syntax_1(text)
    if temp:
        result += temp
    # else:
    temp = syntax_2(text)
    if temp:
        result += temp
    # else:
    temp = syntax_3(text)
    if temp:
        result += temp
    # else:
    temp = syntax_4(text)
    if temp:
        result += temp

    return result


def syntax_1(text):
    match = (
        r"^.*? error\s*> (.*?) error on line ([0-9]+) in file (.*?): ! (.*?)"
        r"\n\nl\.[0-9]+\s*\\([^\s]+)"
    )
    error = re.search(match, text, flags=re.MULTILINE)
    if error:
        class_, line, _, desc, sub_desc = error.groups()
        template = "  - line {}, {} error: {} \\{}\n"
        return template.format(line, translate_class(class_), desc, sub_desc)
    return None


def syntax_2(text):
    match = (
        r"^.*? error\s*> (.*?) error on line ([0-9]+) in file (.*?):"
        r"\n\n\[ctxlua\]:[0-9]*: (.*?)$"
    )
    error = re.search(match, text, flags=re.MULTILINE)
    if error:
        class_, line, _, desc = error.groups()
        template = "  - line {}, {} error: {}\n"
        return template.format(line, translate_class(class_), desc)
    return None


def syntax_3(text):
    match = \
        r"^.*? error\s*> (.*?) error on line ([0-9]+) in file (.*?): ! (.*?)$"
    error = re.search(match, text, flags=re.MULTILINE)
    if error:
        class_, line, _, desc = error.groups()
        template = "  - line {}, {} error: {}\n"
        return template.format(line, translate_class(class_), desc)
    return None


def syntax_4(text):
    match = \
        r"^.*? error\s*> (.*?) error on line ([0-9]+) in file (.*?):$"
    error = re.search(match, text, flags=re.MULTILINE)
    if error:
        class_, line, _ = error.groups()
        template = "  - line {}, {} error\n"
        return template.format(line, translate_class(class_))
    return None
