import re


MODULE = r"use(lua|tex)?module"

CONDITIONAL_A = \
    r"[a-zA-Z]*doif[a-zA-Z]*(else)?|[a-zA-Z]*doif(else)?[[a-zA-Z]]*"

CONDITIONAL_B = \
    r"if[[:alpha:]]*|[[:alpha:]]*(true|false)|loop|repeat|then|or|else|fi"


def control_sequence(text):
    try:
        if (
            text.startswith("start") or text.startswith("stop") or
            re.match(MODULE, text) or re.match(CONDITIONAL_A, text) or
            re.match(CONDITIONAL_B, text)
        ):
            return "<sfl>\\</sfl><flo>{}</flo>".format(text)
        else:
            return "<sco>\\</sco><con>{}</con>".format(text)
    except AttributeError as e:
        print("err", text)
        raise e


def unescape(text):
    return text.replace("&gt;", ">").replace("&lt;", "<").replace(
        "&nbsp;", " ").replace("<br>", "\n")


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
    return unescape(
        strip_tags(text.replace("<br>", "\n")).replace("&nbsp;", " ")
    )


def strip_css_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
