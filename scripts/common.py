import sublime
import json
import os
import re


def file_with_ext(file, ext):
    return os.path.splitext(os.path.basename(file))[0] + ext


def deep_update(main, new):
    for k, v in new.items():
        if isinstance(v, dict):
            if k not in main:
                main[k] = {}
            deep_update(main[k], v)
        else:
            main[k] = v


def is_context(view):
    try:
        return view.match_selector(
            view.sel()[0].begin(), "text.tex.context")
    except:
        return False


def load_commands(path_, version):
    name = "commands {}.json".format(version)
    commands_json = os.path.join(path_, name)
    with open(commands_json) as f:
        return json.load(f)


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


class ModPath:
    def __init__(self, path):
        self.new = path
        self.orig = os.environ["PATH"]

    def __enter__(self):
        if isinstance(self.new, str) and self.new:
            new = os.path.abspath(self.new)
            if os.path.exists(new):
                PATH = self.orig.split(os.pathsep)
                if new not in PATH:
                    PATH.insert(0, new)
                else:
                    PATH.remove(new)
                    PATH.insert(0, new)
                os.environ["PATH"] = os.pathsep.join(PATH)

    def __exit__(self, *args):
        os.environ["PATH"] = self.orig


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
        "storage.type.function.general.context",
        "support.function.general.context",
        "keyword.control.conditional.context",
        "keyword.other.alignment.context",
        "entity.name.function.general.context",
        "entity.name.function.symbol.context",
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


# def region_ends_with_command_and_args(view, region):
#     candidate_commands = [
#         command
#         for command in view.find_by_selector(context_command_selector())
#         if region.contains(command)
#     ]
#     if len(candidate_commands) > 0:
#         command = candidate_commands[-1]
#     else:
#         return
#
#     ending_args_sel = "text.tex.context" + \
#         " (meta.braces.context, meta.brackets.context)"
#     match = True
#     for point in range(command.end(), region.end()):
#         if not view.match_selector(point, ending_args_sel):
#             match = False
#             break
#
#     if match:
#         return view.substr(command)[1:]


def reload_settings(self):
    self.settings = sublime.load_settings("ConTeXtTools.sublime-settings")
    self.profile_defaults = self.settings.get("profile_defaults", {})
    self.profiles = self.settings.get("profiles", {})
    self.current_profile_name = self.settings.get("current_profile")
    self.interfaces = self.settings.get("interfaces", {})

    self.profile_names = []
    self.current_profile_index = 0
    for i, profile in enumerate(self.profiles):
        name = profile.get("name")
        self.profile_names.append(name)
        if name == self.current_profile_name:
            self.current_profile_index = i

    inherits = self.profiles[self.current_profile_index].get("inherits")
    if inherits:
        if isinstance(inherits, str):
            inherits = [inherits]
    else:
        inherits = ["profile_defaults"]

    self.current_profile = {}
    for profile_name in inherits:
        if profile_name == "profile_defaults":
            new_settings = self.profile_defaults
        else:
            new_settings = {}
            for profile in self.profiles:
                if profile.get("name") == profile_name:
                    new_settings = profile
                    break
        deep_update(self.current_profile, new_settings)
    deep_update(
        self.current_profile, self.profiles[self.current_profile_index])

    self.current_interface_name = self.current_profile.get(
        "command_popups", {}).get("interface")
    self.current_interface = self.interfaces.get(
        self.current_interface_name, {})


def process_options(name, options, input_, input_base):
    if isinstance(options, str):
        if input_:
            command = [name] + options.split(" ") + [input_]
        else:
            command = [name] + options.split(" ")

    elif isinstance(options, dict):
        command = [name]

        if options.get("result"):
            if input_base:
                output_file_name = sublime.expand_variables(
                    options["result"], {"name": input_base})
                command.append("--result={}".format(output_file_name))
            del options["result"]

        for option, value in options.items():
            if isinstance(value, bool):
                if value:
                    command.append("--{}".format(option))
            elif isinstance(value, dict):
                normalized_value = " ".join(
                    "{}={}".format(k, v) for k, v in value.items())
                command.append("--{}={}".format(option, normalized_value))
            else:
                if option == "script":
                    command.insert(1, "--{}".format(option))
                    command.insert(2, "{}".format(value))
                else:
                    command.append("--{}={}".format(option, value))

        if input_:
            command.append(input_)

    else:
        if input_:
            command = [name, input_]
        else:
            command = [name]

    return command
