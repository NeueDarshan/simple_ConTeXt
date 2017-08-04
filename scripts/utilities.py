import sublime
import subprocess
import itertools
import string
import os
import re


def html_unescape(text):
    return text.replace("&gt;", ">").replace("&lt;", "<").replace(
        "&nbsp;", " ").replace("<br>", "\n")


def html_strip_tags(text):
    return re.sub("<[^<]+>", "", text)


def html_pre_code(text):
    result = ""
    in_tag = False
    for c in text:
        if c == "<":
            result += c
            in_tag = True
        elif c == ">":
            result += c
            in_tag = False
        elif in_tag:
            result += c
        else:
            result += c.replace(" ", "&nbsp;")
    return result.replace("\n", "<br>")


def html_pretty_print(text):
    return text.replace("&nbsp;", " ").replace("<br>", "\n")


def html_raw_print(text):
    return html_unescape(
        html_strip_tags(text.replace("<br>", "\n")).replace("&nbsp;", " ")
    )


def file_with_ext(file, ext):
    return os.path.splitext(os.path.basename(file))[0] + ext


def base_file(file):
    return os.path.splitext(os.path.basename(file))[0]


def file_as_slug(text):
    slug = ""
    for c in text:
        if c in string.ascii_letters + string.digits:
            slug += c.lower()
        else:
            slug += "_"
    return slug


def deep_update(dict_, new_dict):
    for k, v in new_dict.items():
        if isinstance(v, dict):
            if k not in dict_:
                dict_[k] = {}
            deep_update(dict_[k], v)
        else:
            dict_[k] = v


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


def remove_duplicates(list_):
    accum = []
    for obj in list_:
        if obj not in accum:
            accum.append(obj)
    return accum


def type_as_str(obj):
    if isinstance(obj, int):
        return "integer"
    elif isinstance(obj, float):
        return "float"
    elif isinstance(obj, str):
        return "string"
    else:
        return str(type(obj))


def guess_type(text):
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            pass

    if str(text).lower() == "true":
        return True
    elif str(text).lower() == "false":
        return False
    elif str(text).lower() in ["none", "null"]:
        return None
    else:
        return text


def is_context(view):
    return is_scope(view, "text.tex.context")


def is_metapost(view):
    return is_scope(view, "source.metapost")


def is_scope(view, scope):
    return view.match_selector(view.sel()[0].begin(), scope)


def add_path(old, new):
    if isinstance(new, str) and new:
        new = os.path.abspath(new)
        if os.path.exists(new):
            old_path = old.split(os.pathsep)
            if new not in old_path:
                old_path.insert(0, new)
            else:
                old_path.remove(new)
                old_path.insert(0, new)
            return os.pathsep.join(old_path)


def locate(path, file):
    old_path = os.environ["PATH"]
    os.environ["PATH"] = add_path(old_path, path)
    env = os.environ.copy()
    os.environ["PATH"] = old_path
    proc = subprocess.Popen(
        ["mtxrun", "--locate", str(file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    result = proc.communicate()
    return bytes_decode(result[0])


def bytes_decode(text):
    return text.decode(encoding="utf-8", errors="replace").replace(
        "\r\n", "\n").replace("\r", "\n").strip()


def iter_power_set(iter_):
    full = list(iter_)
    return itertools.chain.from_iterable(
        itertools.combinations(full, n) for n in range(len(full) + 1)
    )


def identity(obj):
    return obj


def second_obj(obj):
    return obj[1]


def iter_i_merge_sorted(sorted_iters, key=identity):
    heads = [next(iter_, None) for iter_ in sorted_iters]
    while any(heads):
        i, next_ = min(
            [(i, head) for i, head in enumerate(heads) if head],
            key=second_obj
        )
        yield i, next_
        heads[i] = next(sorted_iters[i], None)


def skip_space(view, point, call=0):
    return view.substr(point).isspace()


def skip_space_nolines(view, point, call=0):
    text = view.substr(point)
    return text.isspace() and text != "\n"


def skip_atmost_one_space_nolines(view, point, call=0):
    if call > 0:
        return False
    else:
        return skip_space_nolines(view, point, call=call)


def skip_nothing(view, point, call=0):
    return False


def skip_args(view, point, call=0):
    if view.substr(point).isspace():
        return True
    elif view.match_selector(point, "meta.braces.context"):
        return True
    elif view.match_selector(point, "meta.brackets.context"):
        return True
    else:
        return False


def last_command_in_view(view, begin=-200, end=None, skip=skip_space_nolines):
    if begin is None:
        start = 0
    elif begin < 0:
        start = end + begin
    else:
        start = begin
    if end is None:
        point = len(view) - 2
    else:
        point = end - 1

    call = 0
    while skip(view, point, call=call):
        call += 1
        point -= 1
        if point < start:
            return
    if not view.match_selector(
        point,
        "meta.other.control.word.context, "
        "punctuation.definition.backslash.context"
    ):
        return

    stop = point + 1
    while view.match_selector(
        point,
        "meta.other.control.word.context "
        "- punctuation.definition.backslash.context"
    ):
        point -= 1
        if point < start:
            return
    return sublime.Region(point, stop)


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


def process_options(name, options, input_, base):
    if isinstance(options, str):
        if input_:
            cmd = [name] + options.split(" ") + [input_]
        else:
            cmd = [name] + options.split(" ")

    elif isinstance(options, dict):
        cmd = [name]

        if options.get("result"):
            if base:
                cmd.append(
                    "--result={}".format(sublime.expand_variables(
                        options["result"], {"name": base}
                    ))
                )
            del options["result"]

        for opt, val in options.items():
            if opt == "mode":
                if any(v for k, v in val.items()):
                    pretty_val = ",".join(k for k, v in val.items() if v)
                    cmd.append("--{}={}".format(opt, pretty_val))
            elif isinstance(val, dict):
                pretty_val = " ".join(
                    "{}={}".format(k, v) for k, v in val.items()
                )
                cmd.append("--{}={}".format(opt, pretty_val))
            elif isinstance(val, bool):
                if val:
                    cmd.append("--{}".format(opt))
            else:
                if opt == "script":
                    cmd.insert(1, "--{}".format(opt))
                    cmd.insert(2, "{}".format(val))
                else:
                    cmd.append("--{}={}".format(opt, val))

        if input_:
            cmd.append(input_)

    else:
        if input_:
            cmd = [name, input_]
        else:
            cmd = [name]

    return cmd
