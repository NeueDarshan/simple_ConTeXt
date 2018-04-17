import xml.etree.ElementTree as ET
import subprocess
import json
import os

from . import files
from . import deep_dict


def parse_lua(file_name, script, opts):
    return parse_common_texlua(file_name, script, opts)


def parse_btx(file_name, script, opts):
    return parse_common_texlua(file_name, script, opts)


def parse_common_texlua(file_name, script, opts):
    kwargs = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "env": {"LUA_PATH": os.path.join(os.path.dirname(script), "?.lua")},
    }
    deep_dict.update(kwargs, opts)
    proc = subprocess.Popen(["texlua", script, file_name], **kwargs)
    result = proc.communicate()
    # code = proc.returncode
    if result:
        try:
            return json.loads(files.decode_bytes(result[0]))
        except ValueError:
            return None
    return None


def parse_xml(file_name):
    with open(file_name) as f:
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

    return result
