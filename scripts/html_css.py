import re


CONTROL_COND_A = \
    r"[a-zA-Z]*doif[a-zA-Z]*(?:else)?|[a-zA-Z]*doif(?:else)?[a-zA-Z]*"

CONTROL_COND_B = r"if[a-zA-Z]*|[a-zA-Z]*(?:true|false)"

CONTROL_MODULE = r"use(?:lua|tex)?module"


def match_exact(regex, text):
    return re.match(r"(?:{})\Z".format(regex), text)


# This approach is a bit odd, seems to work reasonably well though.
CASES = [
    {
        # keyword.control
        "tags": ("flo", "sfl"),
        "f": lambda text:
            text.startswith("start") or
            text.startswith("stop") or
            text in ["loop", "repeat", "then", "or", "else", "fi"] or
            any(match_exact(regex, text) for regex in [
                CONTROL_COND_A, CONTROL_COND_B, CONTROL_MODULE,
            ]),
    },
    {
        # storage.type
        "tags": ("sto", "sst"),
        "f": lambda text: match_exact(r"[xge]?def|g?let|define", text),
    },
    {
        # constant.language
        "tags": ("lan", "sla"),
        "f": lambda text: text in ["relax"],
    },
    {
        # storage.modifier
        "tags": ("mod", "smo"),
        "f": lambda text: text in ["global", "immediate", "the", "outer"],
    },
    {
        # support.function
        "tags": ("con", "sco"),
        "f": lambda _: True,
    },
]


def control_sequence(text):
    try:
        for case in CASES:
            if case["f"](text):
                tags = case["tags"]
                temp = "<{a}>\\</{a}><{b}>%s</{b}>"
                return temp.format(a=tags[1], b=tags[0]) % text
        return ""
    except AttributeError as e:
        # print("err", text)
        raise e


def unescape(text):
    text = text.replace("&gt;", ">").replace("&lt;", "<")
    text = text.replace("&nbsp;", " ").replace("<br>", "\n")
    return text


def strip_tags(text):
    return re.sub("<[^<]+>", "", text)


def protect_space(text):
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


def pretty_print(text):
    return text.replace("&nbsp;", " ").replace("<br>", "\n")


def raw_print(text):
    text = strip_tags(text.replace("<br>", "\n")).replace("&nbsp;", " ")
    return unescape(text)


def strip_css_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
