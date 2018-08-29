from typing import Any, Dict, List, Optional

from . import cite
from . import utilities


def parse(
    text: str, script: str, opts: Dict[str, Any], timeout: float = 5,
) -> Dict[str, List[str]]:
    result = cite.parse_common_luatex(
        text, script, opts, input_as_stdin=True, timeout=timeout,
    )
    return do_format(result)


def do_format(data: Optional[dict]) -> Dict[str, List[str]]:
    result = {"main": [], "errors": []}  # type: Dict[str, List[str]]
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


def compile_errors(errors: List[List[str]]) -> str:
    result = ""
    for err in errors:
        if len(err) > 2:
            result += "".join("  - line {}, {}: {}\n".format(*err))
    return result
