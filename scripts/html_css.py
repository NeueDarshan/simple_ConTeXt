import re

from typing import TypeVar


T = TypeVar("T")

CONTROL_COND_A = \
    r"[a-zA-Z]*doif[a-zA-Z]*(?:else)?|[a-zA-Z]*doif(?:else)?[a-zA-Z]*"

CONTROL_COND_B = r"if[a-zA-Z]*|[a-zA-Z]*(?:true|false)"

CONTROL_MODULE = r"use(?:lua|tex)?module"


def match_exact(regex: str, text: str) -> bool:
    return bool(re.match(r"(?:{})\Z".format(regex), text))


# This approach is a bit odd, works reasonably well though.
CASES = {
    (
        # `keyword.control`
        ("flo", "sfl"),
        lambda text:
            text.startswith("start") or
            text.startswith("stop") or
            text in {"loop", "repeat", "then", "or", "else", "fi"} or
            any(match_exact(regex, text) for regex in {
                CONTROL_COND_A, CONTROL_COND_B, CONTROL_MODULE,
            }),
    ),
    (
        # `storage.type`
        ("sto", "sst"),
        lambda text: match_exact(r"[xge]?def|g?let|define", text),
    ),
    (
        # `constant.language`
        ("lan", "sla"),
        lambda text: text == "relax",
    ),
    (
        # `storage.modifier`
        ("mod", "smo"),
        lambda text: text in {"global", "immediate", "the", "outer"},
    ),
    (
        # `support.function`
        ("con", "sco"),
        lambda _: True,
    ),
}


def control_sequence(text: str) -> str:
    try:
        for case in CASES:
            if case[1](text):
                tags = case[0]
                temp = "<{a}>\\</{a}><{b}>%s</{b}>"
                return temp.format(a=tags[1], b=tags[0]) % text
        return ""
    except AttributeError as e:
        print("[simple_ConTeXt] err:", text)
        raise e


def unescape(text: str) -> str:
    text = text.replace("&gt;", ">").replace("&lt;", "<")
    return text.replace("&nbsp;", " ").replace("<br>", "\n")


def strip_tags(data: T) -> T:
    if isinstance(data, str):
        return re.sub("<[^<]+>", "", data)
    elif isinstance(data, list):
        return [strip_tags(x) for x in data]
    elif isinstance(data, tuple):
        return tuple(strip_tags(x) for x in data)
    elif isinstance(data, dict):
        return {strip_tags(k): strip_tags(v) for k, v in data.items()}
    return data


def protect_space(text: str) -> str:
    result = ""
    in_tag = False
    for c in text:
        if c == "<":
            result += c
            in_tag = True
        elif c == ">":
            result += c
            in_tag = False
        elif in_tag:
            result += c
        else:
            result += c.replace(" ", "&nbsp;")
    return result.replace("\n", "<br>")


def pretty_print(text: str) -> str:
    return text.replace("&nbsp;", " ").replace("<br>", "\n")


def raw_print(text: str) -> str:
    text = strip_tags(text.replace("<br>", "\n")).replace("&nbsp;", " ")
    return unescape(text)


def strip_css_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
