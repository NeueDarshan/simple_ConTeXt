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
    return view.match_selector(view.sel()[0].begin(), "text.tex.context")


def load_commands(path_, version):
    with open(os.path.join(path_, "commands {}.json".format(version))) as f:
        return json.load(f)


def protect_html_whitespace(string):
    return string.replace(" ", "&nbsp;").replace("\n", "<br />")


# we use <u> style markup to indicate default arguments in the json files,
# so we give special attention to preserving those tags
def protect_html_brackets(string, ignore_tags=["u"]):
    protected = string.replace("<", "&lt;").replace(">", "&gt;")
    for tag in ignore_tags:
        protected = protected.replace(
            "&lt;{}&gt;".format(tag), "<{}>".format(tag)
        )
        protected = protected.replace(
            "&lt;/{}&gt;".format(tag), "</{}>".format(tag)
        )
    return protected


def protect_html(string, ignore_tags=["u"]):
    return protect_html_whitespace(
        protect_html_brackets(string, ignore_tags=ignore_tags)
    )


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

    def _is_error(line):
        return re.match(
            r"^.*?>\s*(.*?)\s+error\s+on\s+line\s+([0-9]+).*?!\s*(.*?)$",
            line
        )

    def _is_code_snippet(line):
        return re.match(r"^\s*[0-9]+", line)

    def _is_blank_line(line):
        return len(line) == 0 or re.match(r"^\s*$", line)

    start_of_error = 0
    log = file_str.split("\n")
    for i, line in enumerate(log):
        error = _is_error(line)
        if error:
            error_summary = "{} error on line {}: {}".format(*error.groups())
            start_of_error = i + 1
            break

    while _is_blank_line(log[start_of_error]):
        start_of_error += 1

    cur_line = start_of_error
    while not _is_code_snippet(log[cur_line]):
        cur_line += 1
    end_of_error = cur_line

    while _is_blank_line(log[end_of_error]):
        end_of_error -= 1

    return "\n\n".join([error_summary] + log[start_of_error:end_of_error - 1])


def commands_in_view(view, begin=None, end=None):
    blocks = view.find_by_selector("meta.other.control.word.context")
    starts = [
        p for p in view.find_by_selector(
            "meta.other.control.word.context "
            "punctuation.definition.backslash.context"
        )
    ]

    words = []
    for i, s in enumerate(starts):
        a = s.begin()
        try:
            b = starts[i+1].begin()
        except IndexError:
            b = len(view)
        for w in blocks:
            if w.intersects(s):
                b = min(b, w.end())
        words.append(sublime.Region(a, b))

    def _filter(w, begin=None, end=None):
        if begin is not None and w.begin() < begin:
            return False
        elif end is not None and w.end() > end:
            return False
        else:
            return True

    return [w for w in words if _filter(w, begin=begin, end=end)]


def last_command_in_view(view, begin=None, end=None):
    try:
        return commands_in_view(view, begin=begin, end=end)[-1]
    except IndexError:
        return


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
        self.current_profile, self.profiles[self.current_profile_index]
    )

    self.current_interface_name = self.current_profile.get(
        "command_popups", {}).get("interface")
    self.current_interface = self.interfaces.get(
        self.current_interface_name, {}
    )


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
                    options["result"], {"name": input_base}
                )
                command.append("--result={}".format(output_file_name))
            del options["result"]

        for option, value in options.items():
            if isinstance(value, bool):
                if value:
                    command.append("--{}".format(option))
            elif isinstance(value, dict):
                normalized_value = " ".join(
                    "{}={}".format(k, v) for k, v in value.items()
                )
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
