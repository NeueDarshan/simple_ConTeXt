import re


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
