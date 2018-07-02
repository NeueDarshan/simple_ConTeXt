from . import cite
from . import utilities


def parse(text, script, opts, timeout=5):
    result = cite.parse_common_luatex(
        text, script, opts, input_as_stdin=True, timeout=timeout,
    )
    return do_format(result)


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
