import sublime
import json
import os
import re


def file_with_ext(file, ext):
    return os.path.splitext(os.path.basename(file))[0] + ext


def is_context(view):
    try:
        return view.match_selector(
            view.sel()[0].begin(), "text.tex.context")
    except:
        return False


def load_commands(path_, profile):
    try:
        version = profile.get("command_popups", {}).get("version")
        if not version:
            version = "Minimals"
        name = "commands {version}.json".format(version=version)
        commands_json = os.path.join(path_, name)
        with open(commands_json) as f:
            return json.load(f)
    except FileNotFoundError:
        return


def protect_html_whitespace(string):
    return string.replace(" ", "&nbsp;").replace("\n", "<br />")


# we use <u> style markup to indicate default arguments in the json files,
# so we give special attention to preserving those tags
def protect_html_brackets(string, ignore_tags=["u"]):
    new_string = string.replace("<", "&lt;").replace(">", "&gt;")
    for tag in ignore_tags:
        new_string = new_string.replace(
            "&lt;{tag}&gt;".format(tag=tag),
            "<{tag}>".format(tag=tag))
        new_string = new_string.replace(
            "&lt;/{tag}&gt;".format(tag=tag),
            "</{tag}>".format(tag=tag))
    return new_string


def protect_html(string, ignore_tags=["u"]):
    return protect_html_whitespace(
        protect_html_brackets(string, ignore_tags=ignore_tags))


def prep_environ_path(profile):
    context_path = profile.get("context_executable", {}).get("path")
    if not context_path:
        return
    context_path = os.path.normpath(context_path)

    passes_initial_check = isinstance(context_path, str) \
        and os.path.exists(context_path)
    if passes_initial_check:
        PATH = os.environ["PATH"].split(os.pathsep)
        if context_path not in PATH:
            PATH.insert(0, context_path)
        else:
            PATH.remove(context_path)
            PATH.insert(0, context_path)
        os.environ["PATH"] = os.pathsep.join(PATH)


def parse_log_for_error(file_bytes):
    file_str = file_bytes.decode(encoding="utf-8")
    file_str = file_str.replace("\r\n", "\n").replace("\r", "\n")

    def is_error(line):
        return re.match(
            r"^.*?>\s*(.*?)\s+error\s+on\s+line\s+([0-9]+).*?!\s*(.*?)$",
            line)

    def is_code_snippet(line):
        return re.match(r"^\s*[0-9]+", line)

    def is_blank_line(line):
        return (len(line) == 0 or re.match(r"^\s*$", line))

    start_of_error = 0
    log = file_str.split("\n")
    for i, line in enumerate(log):
        error = is_error(line)
        if error:
            error_summary = "{} error on line {}: {}".format(*error.groups())
            start_of_error = i + 1
            break

    while is_blank_line(log[start_of_error]):
        start_of_error += 1

    cur_line = start_of_error
    while not is_code_snippet(log[cur_line]):
        cur_line += 1
    end_of_error = cur_line

    while is_blank_line(log[end_of_error]):
        end_of_error -= 1

    return "\n\n".join([error_summary] + log[start_of_error:end_of_error - 1])


def context_command_selector():
    return ", ".join([
        "support.function.control-word.context",
        "keyword.control-word.context",
        "entity.control-word.tex.context"
    ])


def last_command_in_region(view, region):
    candidate_commands = [
        command
        for command in view.find_by_selector(context_command_selector())
        if region.contains(command)
    ]
    if len(candidate_commands) > 0:
        command = candidate_commands[-1]
        tail = view.substr(sublime.Region(command.end(), region.end()))
        return view.substr(command)[1:], tail
    return None, None
