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
    if version:
        ver, fmt, int_ = version.groups()
    else:
        ver, fmt, int_ = None, None, None

    pages = re.search(
        r"mkiv lua stats\s*>.*?([0-9]+) shipped pages", string
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
                r" in file .*?: ! Undefined control sequence\n+l\.[0-9]+ "
                r"(\\[a-zA-Z]+)",
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
        "system": {
            "version": ver,
            "format": fmt,
            "interface": int_,
        },
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
