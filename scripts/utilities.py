import sublime

import itertools
import collections
import re
import os

from . import randomize
from . import files


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


def get_variables(self):
    variables = self.window.extract_variables()

    variables["simple_context_path_sep"] = re.escape(os.path.sep)

    env = os.environ.copy()
    if self._path and os.path.exists(self._path):
        variables["simple_context_prefixed_path"] = \
            files.add_path(env["PATH"], self._path)
    else:
        variables["simple_context_prefixed_path"] = env["PATH"]

    name = self._PDF.get("viewer")
    viewer = self._PDF_viewers.get(name)
    variables["simple_context_pdf_viewer"] = viewer if viewer else ""

    return variables


def expand_variables(self, args, variables):
    result = _expand_variables(self, args, variables)
    return sublime.expand_variables(result, variables)


def _expand_variables(self, args, variables):
    if isinstance(args, dict):
        return {
            k: _expand_variables(self, v, variables) for k, v in args.items()
        }
    elif isinstance(args, list):
        result = []
        for x in args:
            if x == "$simple_context_insert_options":
                result += process_options(
                    self, self._program.get("options", {}), variables
                )
            else:
                result.append(_expand_variables(self, x, variables))
        return result
    else:
        return args


def process_options(self, options, variables):
    if isinstance(options, str):
        return options.split()

    elif isinstance(options, dict):
        result = []
        if "result" in options:
            result.append(
                "--result={}".format(
                    expand_variables(self, options["result"], variables)
                )
            )
            del options["result"]

        for opt, val in options.items():
            if opt == "mode":
                if any(v for k, v in val.items()):
                    pretty_val = ",".join(k for k, v in val.items() if v)
                    result.append("--{}={}".format(opt, pretty_val))
            elif isinstance(val, dict):
                pretty_val = " ".join(
                    "{}={}".format(k, v) for k, v in val.items()
                )
                result.append("--{}={}".format(opt, pretty_val))
            elif isinstance(val, bool):
                if val:
                    result.append("--{}".format(opt))
            else:
                if opt == "script":
                    result.insert(1, "--{}".format(opt))
                    result.insert(2, "{}".format(val))
                else:
                    result.append("--{}={}".format(opt, val))
        return result

    else:
        return []


class Choice:
    def __init__(self, options, choice=0):
        self.options = sorted(options)
        self.set(choice)

    def set(self, choice):
        if isinstance(choice, int):
            self.choice = choice
        else:
            try:
                self.choice = self.options.index(choice)
            except ValueError:
                self.choice = 0

    def get(self):
        return self.options[self.choice]

    def to_list(self, string=False):
        choice = self.get()
        if string:
            return [[k, str(k == choice)] for k in self.options]
        else:
            return [[k, k == choice] for k in self.options]

    def __str__(self):
        return " ".join(self.options)


class LeastRecentlyUsedCache:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = collections.OrderedDict()

    def __setitem__(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key, last=False)
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=True)

    def __getitem__(self, key):
        return self.cache[key]

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)

    def clear(self):
        self.cache.clear()


class FuzzyOrderedDict:
    def __init__(self, iterable=[], max_size=100):
        self.max_size = max_size
        self.cache = collections.deque(iterable, max_size)

    def add_left(self, *args):
        if len(args) == 1:
            self._add_left(*args)
        elif len(args) == 2:
            self._add_left([args])

    def _add_left(self, args):
        for k, v in reversed(args):
            self.cache.appendleft([k, v])

    def fuzzy_add_right(self, *args):
        if len(args) == 1:
            self._fuzzy_add_right(*args)
        elif len(args) == 2:
            self._fuzzy_add_right([args])

    def _fuzzy_add_right(self, args):
        max_len = self.cache.maxlen
        cur_len = len(self.cache)
        add_len = len(args)
        add_amt = min(add_len, max_len - cur_len)

        for k, v in args[:add_amt]:
            self.cache.append((k, v))

        indices = set()
        for k, v in reversed(args[add_amt:]):
            i = max_len - 1 - randomize.poly_biased_randint(
                0, max_len - 1, ignore=indices, power=3
            )
            self.cache[i] = (k, v)
            indices.add(i)

    def __iter__(self):
        return iter(self.cache)

    def __contains__(self, key):
        return key in [k for k, v in self]

    def __getitem__(self, key):
        for k, v in self:
            if key == k:
                return v
        else:
            raise KeyError

    def __len__(self):
        return len(self.cache)

    def __str__(self):
        return str(self.cache)
