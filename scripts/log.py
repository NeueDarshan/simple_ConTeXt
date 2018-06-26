from . import cite
from . import utilities


def parse(text, script, opts, timeout=5):
    # text = text.decode(encoding="utf-8", errors="ignore")
    # text = text.replace("\r\n", "\n").replace("\r", "\n")
    return cite.parse_common_texlua(
        text, script, opts, input_as_stdin=True, timeout=timeout,
    )


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
