import subprocess
import string
import re
import os


CREATE_NO_WINDOW = 0x08000000


def fuzzy_locate(path, file_, flags=0, methods=[None], extensions=[""]):
    for method in methods:
        for ext in extensions:
            text = locate(
                path, "{}{}".format(file_, ext), flags=flags, methods=[method],
            )
            if text:
                return text
    return None


def locate(path, file_, flags=0, methods=[None]):
    for method in methods:
        if method is None:
            environ = os.environ.copy()
            environ["PATH"] = add_path(environ["PATH"], path)
            try:
                proc = subprocess.Popen(
                    ["mtxrun", "--locate", file_],
                    creationflags=flags,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=environ,
                )
                result = proc.communicate()
                return clean_output(decode_bytes(result[0]))
            except OSError:
                return None
        else:
            if os.path.sep in file_:
                dir_, name = os.path.split(file_)
                for root, _, files in os.walk(
                    os.path.normpath(os.path.join(method, dir_))
                ):
                    if name in files:
                        return os.path.normpath(os.path.join(root, name))
            else:
                for root, _, files in os.walk(os.path.normpath(method)):
                    if file_ in files:
                        return os.path.normpath(os.path.join(root, file_))
    return None


def decode_bytes(text):
    text = text.decode(encoding="utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return text


def clean_output(text):
    return re.sub(
        r"resolvers\s*[>|]\s*trees\s*[>|]\s*analyzing\s*'home:texmf'",
        "",
        text,
    ).strip()


def parse_checker(text, tolerant=True):
    text = clean_output(text).replace(" <cr> " + " <lf> ", " <lf> ")
    text = text.replace(" <cr> ", " <lf> ").replace(" <lf> ", "\n")
    if text == "no error":
        return {"passed": True}
    elif text == "no file":
        return {"passed": tolerant}

    parts = text.split("  ", maxsplit=2)
    if len(parts) == 3:
        line_stop, head, main = parts
        match = re.search(r"\(see line ([0-9]+)\)\Z", main)
        if match:
            line_start = match.group(1)
            main = main[:match.start()]
            return {
                "passed": False,
                "head": head,
                "main": main,
                "start": line_start,
                "stop": line_stop,
            }
        return {
            "passed": False, "head": head, "main": main, "stop": line_stop,
        }
    return {"passed": tolerant}


def add_path(old, new):
    if isinstance(new, str) and new:
        new = os.path.abspath(new)
        if os.path.exists(new):
            old_path = old.split(os.pathsep)
            if new not in old_path:
                old_path.insert(0, new)
            else:
                old_path.remove(new)
                old_path.insert(0, new)
            return os.pathsep.join(old_path)
    return old


def file_as_slug(text):
    slug = ""
    if text:
        for c in text:
            if c in string.ascii_letters + string.digits:
                slug += c.lower()
            else:
                slug += "_"
    return slug


def file_with_ext(file_, ext):
    return os.path.splitext(file_)[0] + ext


def base_file(file_):
    return os.path.splitext(file_)[0]
