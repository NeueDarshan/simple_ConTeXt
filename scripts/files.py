import functools
import os
import re
import subprocess
import zlib


CREATE_NO_WINDOW = 0x08000000


@functools.lru_cache(maxsize=256)
def fuzzy_locate(
    path,
    file_,
    flags=0,
    shell=False,
    methods=None,
    extensions=None,
    timeout=5,
):
    methods = (None,) if methods is None else methods
    extensions = ("",) if extensions is None else extensions
    for method in methods:
        for ext in extensions:
            text = locate(
                path,
                file_ + ext,
                flags=flags,
                shell=shell,
                methods=(method,),
                timeout=timeout,
            )
            if text:
                return text
    return None


@functools.lru_cache(maxsize=256)
def locate(path, file_, flags=0, shell=False, methods=None, timeout=5):
    methods = (None,) if methods is None else methods
    for method in methods:
        if method is None:
            environ = os.environ.copy()
            environ["PATH"] = add_path(environ["PATH"], path)
            try:
                proc = subprocess.Popen(
                    ["mtxrun", "--locate", file_],
                    creationflags=flags,
                    shell=shell,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=environ,
                )
                result = proc.communicate(timeout=timeout)
                if result:
                    return clean_output(decode_bytes(result[0]))
            except (subprocess.TimeoutExpired, OSError):
                pass

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
    regex = r"resolvers\s*[>|]\s*trees\s*[>|]\s*analyzing\s*'home:texmf'"
    return re.sub(regex, "", text).strip()


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
    if isinstance(text, str):
        return hex(zlib.adler32(bytes(text, "utf-8")))
    return "default"
