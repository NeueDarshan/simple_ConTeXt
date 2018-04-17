import subprocess
import json

from . import files


def parse_lua(file_name, script, opts):
    kwargs = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
    }
    kwargs.update(opts)
    proc = subprocess.Popen(["texlua", script, file_name], **kwargs)
    result = proc.communicate()
    # code = proc.returncode
    if result:
        try:
            return json.loads(files.decode_bytes(result[0]))
        except ValueError:
            return None
    return None


def parse_bib(file_name, script, opts):
    return None


def parse_xml(file_name, opts):
    return None
