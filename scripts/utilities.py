import sublime
import subprocess
import itertools
import string
import os
import re


def html_unescape(s):
    return s.replace("&gt;", ">").replace("&lt;", "<").replace(
        "&nbsp;", " ").replace("<br>", "\n")


def html_strip_tags(s):
    return re.sub("<[^<]+>", "", s)


def html_pre_code(s):
    res = ""
    in_tag = False
    for c in s:
        if c == "<":
            res += c
            in_tag = True
        elif c == ">":
            res += c
            in_tag = False
        elif in_tag:
            res += c
        else:
            res += c.replace(" ", "&nbsp;")
    return res.replace("\n", "<br>")


def html_pretty_print(s):
    return s.replace("&nbsp;", " ").replace("<br>", "\n")


def html_raw_print(s):
    return html_unescape(
        html_strip_tags(s.replace("<br>", "\n")).replace("&nbsp;", " ")
    )


def file_with_ext(file, ext):
    return os.path.splitext(os.path.basename(file))[0] + ext


def base_file(file):
    return file_with_ext(file, "")


def file_as_slug(s):
    slug = ""
    for c in s:
        if c in string.ascii_letters + string.digits:
            slug += c.lower()
        else:
            slug += "_"
    return slug


def deep_update(main, new):
    for k, v in new.items():
        if isinstance(v, dict):
            if k not in main:
                main[k] = {}
            deep_update(main[k], v)
        else:
            main[k] = v


def iter_deep(dict_):
    for k, v in dict_.items():
        if isinstance(v, dict):
            for key, val in iter_deep(v):
                yield [k] + key, val
        else:
            yield [k], v


def get_deep(dict_, keys):
    if len(keys) == 0:
        return dict_
    elif len(keys) == 1:
        return dict_[keys[0]]
    else:
        return get_deep(dict_[keys[0]], keys[1:])


def get_deep_safe(dict_, keys):
    if len(keys) == 0:
        return dict_
    elif len(keys) == 1:
        return dict_.get(keys[0])
    else:
        dict_.setdefault(keys[0], {})
        return get_deep_safe(dict_[keys[0]], keys[1:])


def set_deep(dict_, keys, value):
    if len(keys) <= 1:
        dict_[keys[0]] = value
    else:
        set_deep(dict_[keys[0]], keys[1:], value)


def set_deep_safe(dict_, keys, value):
    if len(keys) <= 1:
        dict_[keys[0]] = value
    else:
        dict_.setdefault(keys[0], {})
        set_deep_safe(dict_[keys[0]], keys[1:], value)


def in_deep(dict_, keys):
    if len(keys) <= 1:
        return (keys[0] in dict_)
    else:
        return in_deep(dict_[keys[0]], keys[1:])


def del_deep(dict_, keys):
    if len(keys) <= 1:
        del dict_[keys[0]]
    else:
        del_deep(dict_[keys[0]], keys[1:])


def del_deep_safe(dict_, keys):
    if len(keys) <= 1:
        try:
            del dict_[keys[0]]
        except KeyError:
            pass
    else:
        dict_.setdefault(keys[0], {})
        del_deep_safe(dict_[keys[0]], keys[1:])


def deduplicate(list_):
    new = []
    for e in list_:
        if e not in new:
            new.append(e)
    return new


def type_as_str(obj):
    if isinstance(obj, int):
        return "integer"
    elif isinstance(obj, float):
        return "float"
    elif isinstance(obj, str):
        return "string"
    else:
        return str(type(obj))


def guess_type(string):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            pass

    if str(string).lower() == "true":
        return True
    elif str(string).lower() == "false":
        return False
    elif str(string).lower() in ["none", "null"]:
        return None
    else:
        return string


def is_context(view):
    return view.match_selector(view.sel()[0].begin(), "text.tex.context")


def add_path(orig, new):
    if isinstance(new, str) and new:
        new = os.path.abspath(new)
        if os.path.exists(new):
            PATH = orig.split(os.pathsep)
            if new not in PATH:
                PATH.insert(0, new)
            else:
                PATH.remove(new)
                PATH.insert(0, new)
            return os.pathsep.join(PATH)


def locate(path, file):
    orig_path = os.environ["PATH"]
    os.environ["PATH"] = add_path(orig_path, path)
    env = os.environ.copy()
    os.environ["PATH"] = orig_path
    proc = subprocess.Popen(
        ["mtxrun", "--locate", str(file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    result = proc.communicate()
    return result[0].decode(encoding="utf-8", errors="replace").replace(
        "\r\n", "\n").replace("\r", "\n").strip()


def iter_power_set(iterable):
    list_ = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(list_, n) for n in range(len(list_) + 1)
    )


def iter_i_merge_sorted(sorted_iters, key=lambda x: x):
    tops = [next(iter_, None) for iter_ in sorted_iters]
    while any(tops):
        i, next_ = min(
            [(i, top) for i, top in enumerate(tops) if top],
            key=lambda t: key(t[1])
        )
        yield i, next_
        tops[i] = next(sorted_iters[i], None)


def _skip_space(v, p):
    return v.substr(p).isspace()


def _skip_space_nolines(v, p):
    str_ = v.substr(p)
    return str_.isspace() and str_ != "\n"


def _skip_args(v, p):
    if v.substr(p).isspace():
        return True
    elif v.match_selector(p, "meta.braces.context"):
        return True
    elif v.match_selector(p, "meta.brackets.context"):
        return True
    else:
        return False


def last_command_in_view(view, begin=-200, end=None, skip=_skip_space_nolines):
    if begin is None:
        start = 0
    elif begin < 0:
        start = end + begin
    else:
        start = begin

    if end is None:
        p = len(view) - 2
    else:
        p = end - 1

    while skip(view, p):
        p -= 1
        if p < start:
            return

    if not view.match_selector(
        p,
        "meta.other.control.word.context, "
        "punctuation.definition.backslash.context"
    ):
        return

    stop = p + 1
    while view.match_selector(
        p,
        "meta.other.control.word.context "
        "- punctuation.definition.backslash.context"
    ):
        p -= 1
        if p < start:
            return

    return sublime.Region(p, stop)


def reload_settings(self):
    self._sublime_settings = \
        sublime.load_settings("simple_ConTeXt.sublime-settings")
    self._paths = self._sublime_settings.get("paths", {})
    self._PDF_viewers = self._sublime_settings.get("PDF_viewers", {})
    self._settings = self._sublime_settings.get("settings", {})
    self._setting_groups = self._sublime_settings.get("setting_groups", {})

    self._path = self._settings.get("path")
    if self._path in self._paths:
        self._path = self._paths[self._path]

    self._PDF = self._settings.get("PDF", {})
    self._pop_ups = self._settings.get("pop_ups", {})
    self._references = self._settings.get("references", {})

    self._builder = self._settings.get("builder", {})
    self._program = self._builder.get("program", {})
    self._check = self._builder.get("check", {})


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
            if option == "mode":
                if any(v for k, v in value.items()):
                    normalized_value = \
                        ",".join(k for k, v in value.items() if v)
                    command.append("--{}={}".format(option, normalized_value))
            elif isinstance(value, dict):
                normalized_value = " ".join(
                    "{}={}".format(k, v) for k, v in value.items()
                )
                command.append("--{}={}".format(option, normalized_value))
            elif isinstance(value, bool):
                if value:
                    command.append("--{}".format(option))
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
