import ast
import errno
import os
import re
import string
import subprocess
import xml.etree.ElementTree as ET

from . import deep_dict
from . import files


class DefaultFormatter(string.Formatter):
    def __init__(self, handler=None):
        self._handler = handler

    def get_value(self, key, args, kwargs):
        if key not in kwargs and self._handler:
            kwargs[key] = self._handler(key)
        return super().get_value(key, args, kwargs)


def parse_lua(file_name, script, opts):
    result = parse_common_luatex(file_name, script, opts)
    return normalize_dict(result)


def parse_btx(file_name, script, opts):
    result = parse_common_luatex(file_name, script, opts)
    return normalize_dict(result)


def parse_common_luatex(input_, script, opts, input_as_stdin=False, timeout=5):
    kwargs = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "env": {"LUA_PATH": os.path.join(os.path.dirname(script), "?.lua")},
    }
    deep_dict.update(kwargs, opts)
    if input_as_stdin:
        call = ["luatex", "--luaonly", script]
        comm = {"timeout": timeout, "input": input_}
    else:
        call = ["luatex", "--luaonly", script, input_]
        comm = {"timeout": timeout}
    proc = subprocess.Popen(call, **kwargs)
    try:
        output = proc.communicate(**comm)
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
        try:
            return ast.literal_eval(text)
        except ValueError:
            return None
    return None


def parse_xml(file_name):
    with open(file_name, encoding="utf-8") as f:
        tree = ET.parse(f)
    root = tree.getroot()
    result = {}

    for child in root:
        if child.tag != "entry":
            continue

        attrib = child.attrib
        tag = attrib.get("tag")
        cat = attrib.get("category")
        if not tag or not cat:
            continue
        entry = {"category": cat}

        for sub in child:
            if sub.tag != "field":
                continue
            name = sub.attrib.get("name")
            if not name:
                continue
            entry[name] = sub.text

        result[tag] = entry

    return normalize_dict(result)


def normalize_dict(data):
    if not data:
        return {}
    return {tag: normalize_dict_aux(entry) for tag, entry in data.items()}


def normalize_dict_aux(data):
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            k = k.lower() if isinstance(k, str) else k
            if k == "category" and isinstance(v, str):
                v = v.lower()
            else:
                v = normalize_dict_aux(v)
            result[k] = v
        return result
    elif isinstance(data, (int, float)) and not isinstance(data, bool):
        return str(data)
    elif isinstance(data, str):
        return re.sub(r"\s{2,}", " ", data).strip()
    return data
