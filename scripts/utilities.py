import sublime
import itertools


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


def guess_type(obj):
    try:
        return int(obj)
    except ValueError:
        try:
            return float(obj)
        except ValueError:
            if str(obj).lower() == "true":
                return True
            elif str(obj).lower() == "false":
                return False
            elif str(obj).lower() in ["none", "null"]:
                return None
            else:
                return obj


def iter_power_set(iter_):
    full = list(iter_)
    return itertools.chain.from_iterable(
        itertools.combinations(full, n) for n in range(len(full) + 1)
    )


def first_of_one(obj):
    return obj


def second_of_n(obj):
    return obj[1]


def iter_i_merge_sorted(sorted_iters, key=first_of_one):
    stack = [next(iter_, None) for iter_ in sorted_iters]
    while any(stack):
        tops = [(i, top) for i, top in enumerate(stack) if top is not None]
        i, next_ = min(tops, key=key)
        yield i, next_
        stack[i] = next(sorted_iters[i], None)


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
    self._options = self._builder.get("options", {})
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
