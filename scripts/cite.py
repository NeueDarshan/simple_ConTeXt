import ast
import errno
import os
import re
import string
import subprocess
import xml.etree.ElementTree as ET

from typing import Any, Dict, Optional

from . import deep_dict
from . import files


class DefaultFormatter(string.Formatter):
    def __init__(
        self,
        lookup: Optional[Dict[str, str]] = None,
        default: Optional[str] = None,
    ) -> None:
        self._lookup = {} if lookup is None else lookup
        self._default = default

    def get_value(self, key, args, kwargs) -> str:
        if key not in kwargs:
            val = self._lookup.get(key)
            if val is not None:
                kwargs[key] = val
            elif self._default is not None:
                kwargs[key] = self._default
        return super().get_value(key, args, kwargs)


def parse_lua(
    file_name: str, script: str, opts: Dict[str, Any],
) -> Optional[dict]:
    result = parse_common_luatex(file_name, script, opts)
    if result is None:
        return None
    return normalize_dict(result)


def parse_btx(
    file_name: str, script: str, opts: Dict[str, Any],
) -> Optional[dict]:
    result = parse_common_luatex(file_name, script, opts)
    if result is None:
        return None
    return normalize_dict(result)


def parse_common_luatex(
    input_: str,
    script: str,
    opts: Dict[str, Any],
    input_as_stdin: bool = False,
    timeout: float = 5,
) -> Optional[dict]:
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
        out, _ = proc.communicate(**comm)
    except subprocess.TimeoutExpired:
        out = None
    except IOError as e:
        if e.errno == errno.EPIPE:
            out = None
        else:
            raise e
    code = proc.returncode
    if not code and out:
        text = files.decode_bytes(out).strip()
        if text == "nil":
            return None
        try:
            return ast.literal_eval(text)
        except ValueError:
            return None
    return None


def parse_xml(file_name: str) -> Optional[dict]:
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
            text = sub.text
            if text is not None:
                entry[name] = text

        result[tag] = entry

    return normalize_dict(result)


def normalize_dict(data: dict) -> dict:
    return {tag: normalize_dict_aux(entry) for tag, entry in data.items()}


def normalize_dict_aux(data):
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if isinstance(k, str):
                k = k.lower()
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
