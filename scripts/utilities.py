import collections
import itertools
import os
import re

from typing import (  # noqa
    Any, Callable, Dict, Iterable, List, Mapping, Optional, Set, TypeVar, Union
)

import sublime

from . import files
from . import randomize
from . import scopes


T = TypeVar("T")

K = TypeVar("K")

V = TypeVar("V")


class HashableDict(dict):
    def __hash__(self) -> int:
        return hash(frozenset(self.items()))


def make_hashable(obj):
    if isinstance(obj, dict):
        result = HashableDict()
        for k, v in obj.items():
            result[k] = make_hashable(v)
        return result
    elif isinstance(obj, list):
        return tuple(make_hashable(x) for x in obj)
    return obj


def hash_first_arg(func: Callable) -> Callable:
    return lambda x, *args, **kwargs: func(make_hashable(x), *args, **kwargs)


def deduplicate_list(list_: List[T]) -> List[T]:
    accum = []  # type: List[T]
    for obj in list_:
        if obj not in accum:
            accum.append(obj)
    return accum


def get_path_var(self) -> Dict[str, Any]:
    copy_ = os.environ.copy()
    if self.context_path and os.path.exists(self.context_path):
        environ = copy_
        environ["PATH"] = files.add_path(environ["PATH"], self.context_path)
        return environ
    return copy_


def guess_type(obj: str) -> Union[int, float, bool, str, None]:
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
            elif str(obj).lower() in {"none", "null"}:
                return None
            return obj


def iter_power_set(iter_: Iterable[T]) -> Iterable[Iterable[T]]:
    full = tuple(iter_)
    return itertools.chain.from_iterable(
        itertools.combinations(full, n) for n in range(len(full) + 1)
    )


def get_path_setting(self, default=None):
    path = self.sublime_settings.get("current.path", "")
    paths = get_setting_location(self, "ConTeXt_paths", default={})
    return paths.get(path, default)


def get_setting(self, opt: str, default=None):
    return self.sublime_settings.get("current.{}".format(opt), default)


def get_setting_location(self, opt: str, default=None):
    return \
        self.sublime_settings.get("program_locations.{}".format(opt), default)


def reload_settings(self) -> None:
    self.sublime_settings = \
        sublime.load_settings("simple_ConTeXt.sublime-settings")
    self.context_path = get_path_setting(self)
    self.prefixed_context_path = expand_variables(
        self, "${simple_context_prefixed_path}", get_variables(self),
    )


def get_variables(self) -> Dict[str, Any]:
    if hasattr(self, "window"):
        variables = self.window.extract_variables()
    elif hasattr(self, "view"):
        window = self.view.window()
        if window:
            variables = window.extract_variables()
        else:
            variables = {}
    else:
        variables = {}

    variables["simple_context_path_sep"] = re.escape(os.path.sep)

    env = os.environ.copy()
    if self.context_path and os.path.exists(self.context_path):
        variables["simple_context_prefixed_path"] = \
            files.add_path(env["PATH"], self.context_path)
    else:
        variables["simple_context_prefixed_path"] = env["PATH"]

    name = get_setting(self, "PDF/viewer")
    viewer = \
        get_setting_location(self, "PDF_viewers", default={}).get(name, "")
    variables["simple_context_pdf_viewer"] = viewer
    variables["simple_context_open_pdf_after_build"] = \
        str(bool(get_setting(self, "PDF/open_after_build")))

    return variables


def expand_variables(self, args, variables: Dict[str, Any]):
    result = _expand_variables(self, args, variables)
    return sublime.expand_variables(result, variables)


def _expand_variables(self, args, variables: Dict[str, Any]):
    if isinstance(args, dict):
        return {
            k: _expand_variables(self, v, variables) for k, v in args.items()
        }
    elif isinstance(args, list):
        result = []  # type: list
        for x in args:
            if x in [
                s % "simple_context_insert_options" for s in ("$%s", "${%s}")
            ]:
                result += process_options(
                    self,
                    get_setting(self, "builder/normal/opts_for_ConTeXt"),
                    variables,
                )
            else:
                result.append(_expand_variables(self, x, variables))
        return result
    elif args in [
        s % "simple_context_open_pdf_after_build" for s in ("$%s", "${%s}")
    ]:
        return bool(get_setting(self, "builder/normal/open_PDF_after_build"))
    elif args in [s % "simple_context_shell" for s in ("$%s", "${%s}")]:
        return bool(self.shell)
    return args


def process_options(
    self,
    options: Union[str, Dict[str, Any]],
    variables: Dict[str, Any],
) -> List[str]:
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
                if any(val.values()):
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
    def __init__(self, options: List[T], choice: int = 0) -> None:
        self.options = sorted(options)
        self.set(choice)

    def set(self, choice: Union[T, int]) -> None:
        if isinstance(choice, int):
            self.choice = choice
        else:
            try:
                self.choice = self.options.index(choice)
            except ValueError:
                self.choice = 0

    def get(self) -> T:
        return self.options[self.choice]

    def to_list(self, string: bool = False) -> List[List[Union[T, str, bool]]]:
        choice = self.get()  # type: T
        if string:
            return [[k, str(k == choice)] for k in self.options]
        return [[k, k == choice] for k in self.options]

    def __str__(self) -> str:
        return "[" + "] [".join(str(x) for x in self.options) + "]"


class LeastRecentlyUsedCache:
    def __init__(self, max_size: int = 100) -> None:
        self.max_size = max_size
        self.cache = collections.OrderedDict()  # type: collections.OrderedDict

    def __setitem__(self, key: K, value: V) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key, last=False)
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=True)

    def __getitem__(self, key: K) -> V:
        return self.cache[key]

    def __contains__(self, key: K) -> bool:
        return key in self.cache

    def __len__(self) -> int:
        return len(self.cache)

    def clear(self) -> None:
        self.cache.clear()


class FuzzyOrderedDict:
    def __init__(
        self,
        iterable: Optional[Iterable] = None,
        max_size: int = 100,
    ) -> None:
        iterable = [] if iterable is None else iterable
        self.max_size = max_size
        self.cache = collections.deque(iterable, max_size)

    def add_left(self, *args) -> None:
        if len(args) == 1:
            self._add_left(*args)
        elif len(args) == 2:
            self._add_left((args,))

    def _add_left(self, args) -> None:
        for k, v in reversed(args):
            self.cache.appendleft((k, v))

    def fuzzy_add_right(self, *args) -> None:
        if len(args) == 1:
            self._fuzzy_add_right(*args)
        elif len(args) == 2:
            self._fuzzy_add_right((args,))

    def _fuzzy_add_right(self, args) -> None:
        max_len = self.cache.maxlen
        cur_len = len(self.cache)
        add_len = len(args)
        add_amt = min(add_len, max_len - cur_len)

        for k, v in args[:add_amt]:
            self.cache.append((k, v))

        indices = set()  # type: Set[int]
        for k, v in reversed(args[add_amt:]):
            i = max_len - 1 - randomize.poly_biased_randint(
                0, max_len - 1, ignore=indices, power=3,
            )
            self.cache[i] = (k, v)
            indices.add(i)

    def __iter__(self):
        return iter(self.cache)

    def __contains__(self, key) -> bool:
        return key in self.cache

    def __getitem__(self, key):
        for k, v in self:
            if key == k:
                return v
        raise KeyError

    def __len__(self) -> int:
        return len(self.cache)

    def __str__(self) -> str:
        return str(self.cache)


class BaseSettings:
    platform = sublime.platform()
    flags = files.CREATE_NO_WINDOW if platform == "windows" else 0
    shell = True if platform == "windows" else False

    def reload_settings(self) -> None:
        reload_settings(self)

    def get_setting(self, opt, default=None):
        return get_setting(self, opt, default=default)

    def is_visible_alt(self) -> bool:
        if hasattr(self, "window"):
            view = self.window.active_view()
            return scopes.is_context(view) if view else False
        elif hasattr(self, "view"):
            return scopes.is_context(self.view)
        return False

    def expand_variables(self, data):
        return expand_variables(self, data, get_variables(self))


class LocateSettings(BaseSettings):
    def reload_settings(self) -> None:
        super().reload_settings()
        try:
            file_name = self.view.file_name()
            self.base_dir = os.path.dirname(file_name) if file_name else None
        except AttributeError:
            self.base_dir = None

    def locate_file_main(
        self,
        name: str,
        extensions: Optional[Iterable[str]] = None,
        timeout: float = 2.5
    ) -> Optional[str]:
        extensions = ("",) if extensions is None else extensions
        if not self.base_dir:
            return None

        methods = (os.path.normpath(self.base_dir),)
        for f in os.listdir(os.path.normpath(self.base_dir)):
            path = os.path.normpath(os.path.join(self.base_dir, f))
            if os.path.isdir(path):
                methods += (path,)
        methods += (os.path.normpath(os.path.join(self.base_dir, "..")),)

        file_ = files.fuzzy_locate(
            self.context_path,
            name,
            flags=self.flags,
            shell=self.shell,
            extensions=extensions,
            methods=methods[::-1],
            timeout=timeout,
        )
        if file_ and os.path.exists(file_):
            return file_

    def locate_file_context(
        self,
        name: str,
        extensions: Optional[Iterable[str]] = None,
        timeout: float = 2.5,
    ) -> Optional[str]:
        extensions = ("",) if extensions is None else extensions
        file_ = files.fuzzy_locate(
            self.context_path,
            name,
            flags=self.flags,
            shell=self.shell,
            extensions=extensions,
            timeout=timeout,
        )
        if file_ and os.path.exists(file_):
            return file_
