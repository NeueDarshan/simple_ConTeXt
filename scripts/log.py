import subprocess
import os

from . import files
from . import deep_dict
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
        class_ = entry[0]
        if class_.endswith("error"):
            errors.append(entry)
        else:
            result["main"].append(entry)
    result["errors"] = utilities.deduplicate_list(errors)
    return result


def compile_errors(errors):
    return "".join("  - {}, line {}: {}\n".format(*err) for err in errors)
