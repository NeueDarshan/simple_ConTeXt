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
    try:
        return view.match_selector(view.sel()[0].begin(), "text.tex.context")
    except:
        return False


def load_commands(path_, version):
    try:
        with open(
            os.path.join(path_, "commands_{}.json".format(version))
        ) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def protect_html_whitespace(string):
    return string.replace(" ", "&nbsp;").replace("\n", "<br />")


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


def _iter_merge_sorted(sorted_iters, key=lambda x: x):
    tops = [next(iter_, None) for iter_ in sorted_iters]
    while any(tops):
        i, next_ = min(
            [(i, top) for i, top in enumerate(tops) if top],
            key=lambda t: key(t[1])
        )
        yield i, next_
        tops[i] = next(sorted_iters[i], None)


def parse_log(bytes_):
    string = bytes_.decode(
        encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    version = re.search(
        r"ConTeXt  ver: (.*?) MKIV .*?  fmt: (.*?)  int: ([^\s]*)", string
    )
    system = {
        "version": version.group(1) if version else None,
        "format": version.group(2) if version else None,
        "interface": version.group(3) if version else None,
    }

    pages = re.search(
        r"^mkiv lua stats\s*> .*? ([0-9]+) shipped pages",
        string,
        flags=re.MULTILINE
    )

    warning_0 = re.finditer(
        r"^((?:Over|Under)full \\hbox) \((.*?)\) in paragraph at lines "
        r"([0-9]+)\-\-([0-9]+)$",
        string,
        flags=re.MULTILINE
    )
    warning_1 = re.finditer(
        r"^((?:Over|Under)full \\vbox) \((.*?)\) (?:detected at line "
        r"([0-9]+))",
        string,
        flags=re.MULTILINE
    )
    warning_2 = re.finditer(
        r"^(system)\s*> command '(.*?)' is already defined",
        string,
        flags=re.MULTILINE
    )
    warning_3 = re.finditer(
        r"^(fonts)\s*> defining > unable to define (.*?)$",
        string,
        flags=re.MULTILINE
    )
    warning_4 = re.finditer(
        r"^(.*?) warning\s*> (.*?)$", string, flags=re.MULTILINE
    )
    warning_5 = re.finditer(
        r"^(.*?)\s*> beware:? (.*?)$", string, flags=re.MULTILINE
    )

    wars = []

    def make_handler(t, s):
        def f(g):
            wars.append({
                "type": t if isinstance(t, str) else g[t],
                "message": s.format(g=g)
            })
        return f

    def handle_warning_1(g):
        if g[2]:
            mess = (
                '"{name}" has occurred at line {line} ({details})'
                .format(name=g[0], line=g[2], details=g[1])
            )
        else:
            mess = (
                '"{name}" has occurred ({details})'
                .format(name=g[0], details=g[1])
            )
        wars.append({"type": "tex", "message": mess})

    handle_warning_0 = make_handler(
        "tex", '"{g[0]}" in paragraph at lines {g[2]}--{g[3]} ({g[1]})'
    )
    handle_warning_2 = make_handler(0, 'command "{g[1]}" is already defined')
    handle_warning_3 = make_handler(0, 'unable to define "{g[1]}"')
    handle_warning_4 = make_handler(0, '{g[1]}')
    handle_warning_5 = make_handler(0, '{g[1]}')

    warning_handler = [
        handle_warning_0, handle_warning_1, handle_warning_2,
        handle_warning_3, handle_warning_4, handle_warning_5
    ]

    for i, warning_match in _iter_merge_sorted(
        [warning_0, warning_1, warning_2, warning_3, warning_4, warning_5],
        key=lambda g: g.start()
    ):
        warning_handler[i](warning_match.groups())

    error_0 = re.finditer(
        r".*? error\s*> (.*?) error on line ([0-9]+)",
        string,
        flags=re.MULTILINE
    )
    error_1 = re.finditer(
        r"(.*?)\s*> error:?",
        string,
        flags=re.MULTILINE
    )

    errs = []

    def handle_error_0(g, tail):
        details = None
        err = g[0]

        if err == "tex":
            search = re.search(
                r" in file .*?: ! Undefined control sequence\n+l\.[0-9]+ .*?"
                r"(\\[a-zA-Z]+)$",
                tail,
                flags=re.MULTILINE
            )
            if search:
                details = (
                    'Undefined control sequence "{}"'.format(search.group(1))
                )
            else:
                search = re.search(r"! (.*?)$", tail, flags=re.MULTILINE)
                details = search.group(1) if search else None
        elif err in ["mp", "metapost"]:
            err = "metapost"
            search = re.search(r"! (.*?)$", tail, flags=re.MULTILINE)
            details = search.group(1) if search else None
        elif err == "lua":
            search = re.search(
                r"\[ctxlua\]:[0-9]+: (.*?)$", tail, flags=re.MULTILINE
            )
            details = search.group(1) if search else None

        errs.append({
            "error": err,
            "line": g[1],
            "details": details
        })

    def handle_error_1(g, tail):
        details = None
        err = g[0]

        if err in ["mp", "metapost"]:
            err = "metapost"
            details = re.search(r"! (.*?)$", tail, flags=re.MULTILINE)
        else:
            details = re.search(r"error:? (.*?)$", tail, flags=re.MULTILINE)

        errs.append({
            "error": err,
            "line": None,
            "details": details.group(1) if details else None
        })

    error_handler = [handle_error_0, handle_error_1]

    for i, error_match in _iter_merge_sorted(
        [error_0, error_1], key=lambda g: g.start()
    ):
        error_handler[i](error_match.groups(), string[error_match.start():])

    return {
        "system": system,
        "warnings": wars,
        "errors": errs,
        "pages": int(pages.group(1)) if pages else None
    }


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

    if not view.match_selector(p, "meta.other.control.word.context"):
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
    self.sublime_settings = \
        sublime.load_settings("ConTeXtTools.sublime-settings")
    self.settings = self.sublime_settings.get("settings", {})
    self.setting_schemes = self.sublime_settings.get("setting_schemes", {})
    self.program_paths = self.sublime_settings.get("program_paths", {})
    self.interfaces = self.sublime_settings.get("interfaces", {})
    self.colour_schemes = self.sublime_settings.get("colour_schemes", {})


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
