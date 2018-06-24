import errno
import os
import subprocess

from . import deep_dict
from . import files
from . import utilities


def parse(text, script, opts, timeout=5):
    # text = text.decode(encoding="utf-8", errors="ignore")
    # text = text.replace("\r\n", "\n").replace("\r", "\n")
    kwargs = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "env": {"LUA_PATH": os.path.join(os.path.dirname(script), "?.lua")},
    }
    deep_dict.update(kwargs, opts)
    proc = subprocess.Popen(
        ["luatex", "--luaonly", script], **kwargs
    )
    try:
        output = proc.communicate(input=text, timeout=timeout)
    except subprocess.TimeoutExpired:
        output = None
    except IOError as e:
        if e.errno == errno.EPIPE:
            output = None
        else:
            raise e
    code = proc.returncode
    if not code and output:
        text = files.decode_bytes(output[0]).strip()
        if text == "nil":
            return None
        # I don't see a problem with this use of \type{eval}, as we have
        # complete control over the string being evaluated.
        result = eval(text)
        return do_format(result)
    return None


def do_format(data):
    result = {"main": [], "errors": []}
    if not isinstance(data, list):
        return result
    errors = []
    for entry in data:
        if not isinstance(entry, list) or not entry:
            continue
        class_ = entry[1]
        if class_.endswith("error"):
            errors.append(entry)
        else:
            result["main"].append(entry)
    result["errors"] = utilities.deduplicate_list(errors)
    return result


def compile_errors(errors):
    result = ""
    for err in errors:
        if len(err) > 2:
            result += "".join("  - line {}, {}: {}\n".format(*err))
    return result
