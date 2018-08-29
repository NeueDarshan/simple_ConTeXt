import ast
# import functools
import json
import os
import re
import threading
import unittest

from typing import Any, Dict, Iterable, List, Optional, Tuple

import sublime
import sublime_plugin

from .scripts import cite
from .scripts import scopes
from .scripts import utilities


BUILT_IN_CITATIONS = (
    r"\A(?:(?:no|use|place|(?:btx)?(?:list|text|always|hidden))?"
    r"cit(?:e|ation))\Z"
)

EXTENSIONS = ("bib", "xml", "lua")

FORMAT = cite.DefaultFormatter(lookup={"year": "????"}, default="??")


def is_citation_start(text: str) -> bool:
    return text == "["


def is_citation_history(cmd: list) -> bool:
    return cmd[0] not in {"left_delete", "right_delete"} if cmd else True


# @utilities.hash_first_arg
# @functools.lru_cache(maxsize=128)
def get_entries(
    bibliographies: Dict[str, Dict[str, Any]],
    format_: List[str],
) -> List[Tuple[str, List[str]]]:
    return sorted(
        [
            (tag, [FORMAT.format(s, tag=tag, **entry) for s in format_])
            for tag, entry in bibliographies.items()
        ],
        key=lambda tup: tup[1][0],
    )


def group_files(files: Iterable[str]) -> Dict[str, List[str]]:
    grouped = {}  # type: Dict[str, List[str]]
    for f in files:
        base, ext = os.path.splitext(f)
        if base in grouped:
            grouped[base].append(f)
        else:
            grouped[base] = [f]
    return {os.path.basename(k): v for k, v in grouped.items()}


class SimpleContextCiteEventListener(
    utilities.LocateSettings, sublime_plugin.ViewEventListener,
):
    extensions = ("",) + tuple(".{}".format(s) for s in EXTENSIONS)
    bibliographies = {}  # type: Dict[str, Optional[dict]]
    bib_per_files = {}  # type: Dict[str, dict]
    lock = threading.Lock()

    def is_visible(self) -> bool:
        return self.is_visible_alt()

    def reload_settings(self) -> None:
        super().reload_settings()
        self.view.window().run_command("simple_context_unpack_lua_scripts")
        self.file_name = str(self.view.file_name())
        self.opts = self.expand_variables(
            {
                "creationflags": self.flags,
                "shell": self.shell,
                "env": {"PATH": "${simple_context_prefixed_path}"},
            }
        )
        self.lua_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_lua.lua"
        )
        self.btx_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_btx.lua"
        )

    def on_modified_async(self) -> None:
        self.reload_settings()
        format_ = self.get_setting("citations/format")
        if isinstance(format_, str):
            format_ = format_.split("<>")
        if not (
            self.is_visible() and self.get_setting("citations/on") and format_
        ):
            return

        sel = self.view.sel()
        if not sel:
            return
        region = sel[0]

        ctrl = scopes.last_block_in_region(
            self.view,
            0,
            scopes.CONTROL_SEQ,
            end=region.begin(),
            skip=scopes.SKIP_ARGS_AND_SPACES,
        )
        if not ctrl:
            return
        last_char = self.view.substr(max(0, region.end() - 1))
        last_cmd = self.view.command_history(0, modifying_only=True)

        if (
            is_citation_start(last_char) and
            is_citation_history(last_cmd) and
            self.is_citation_command(*ctrl)
        ):
            threading.Thread(
                target=lambda: self.do_citation(self.file_name, format_)
            ).start()

    def is_citation_command(self, begin: int, end: int) -> bool:
        name = self.view.substr(sublime.Region(begin, end)).strip()
        user_regex = self.get_setting("citations/command_regex")
        if re.match(BUILT_IN_CITATIONS, name):
            return True
        elif user_regex and re.match(r"\A" + user_regex + r"\Z", name):
            return True
        return False

    def do_citation(self, view_name: str, format_: List[str]) -> None:
        regions = self.view.find_by_selector(scopes.MAYBE_CITATION)
        possible_names = {self.view.substr(r).strip() for r in regions}
        with self.lock:
            for name in possible_names:
                self.try_parse(name, view_name)

        window = self.view.window()
        if window:
            dict_ = {}
            for key, entry in self.bib_per_files.get(view_name, {}).items():
                if key in possible_names:
                    extra = self.bibliographies.get(entry, {})
                    if isinstance(extra, dict):
                        dict_.update(extra)
            self.tags = get_entries(dict_, format_)
            window.show_quick_panel(
                [tup[1] for tup in self.tags], self.on_done,
            )

    def on_done(self, index: int) -> None:
        if 0 <= index < len(self.tags):
            text = self.tags[index]
            if text:
                self.view.run_command(
                    "simple_context_insert_text", {"text": text[0]},
                )

    def try_parse(self, name: str, view_name: str) -> None:
        self.bib_per_files.setdefault(view_name, {})
        if name not in self.bib_per_files[view_name]:
            if view_name:
                main = self.locate_file_main(name, extensions=self.extensions)
                if main:
                    self.bib_per_files[view_name][name] = main
                    bib = self.try_parse_aux(main)
                    if bib is None:
                        msg = "[simple_ConTeXt] failed to parse file: {}"
                        print(msg.format(os.path.basename(main)))
                    self.bibliographies[main] = bib
                    return
            other = self.locate_file_context(name, extensions=self.extensions)
            if other:
                self.bib_per_files[view_name][name] = other
                bib = self.try_parse_aux(other)
                if bib is None:
                    msg = "[simple_ConTeXt] failed to parse file: {}"
                    print(msg.format(os.path.basename(other)))
                self.bibliographies[other] = bib
                return
            self.bib_per_files[view_name][name] = 0

    def try_parse_aux(self, name: str) -> Optional[Dict[str, str]]:
        if name.endswith(".bib"):
            return self.try_parse_btx(name)
        elif name.endswith(".xml"):
            return self.try_parse_xml(name)
        elif name.endswith(".lua"):
            return self.try_parse_lua(name)
        return self.try_parse_btx(name)

    def try_parse_lua(self, name: str) -> Optional[Dict[str, str]]:
        return cite.parse_lua(name, self.lua_script, self.opts)

    def try_parse_btx(self, name: str) -> Optional[Dict[str, str]]:
        return cite.parse_btx(name, self.btx_script, self.opts)

    def try_parse_xml(self, name: str) -> Optional[Dict[str, str]]:
        return cite.parse_xml(name)


class SimpleContextTestParseBibFilesCommand(
    utilities.LocateSettings, sublime_plugin.WindowCommand,
):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.test = TestParseBibFiles(self)

    def run(self) -> None:
        self.reload_settings()
        print("[simple_ConTeXt] - test bib parsing:")
        self.test.test__equivalent_files(self.test_dir)

    def reload_settings(self) -> None:
        super().reload_settings()
        self.window.run_command("simple_context_unpack_lua_scripts")
        self.opts = self.expand_variables(
            {
                "creationflags": self.flags,
                "shell": self.shell,
                "env": {"PATH": "${simple_context_prefixed_path}"},
            }
        )
        self.lua_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_lua.lua"
        )
        self.btx_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_btx.lua"
        )
        self.test_dir = self.expand_variables(
            "${packages}/simple_ConTeXt/tests/bib"
        )

    def try_parse(self, name: str) -> Optional[Dict[str, Any]]:
        if name.endswith(".bib"):
            return self.try_parse_btx(name)
        elif name.endswith(".xml"):
            return self.try_parse_xml(name)
        elif name.endswith(".lua"):
            return self.try_parse_lua(name)
        elif name.endswith(".py"):
            return self.try_parse_py(name)
        return self.try_parse_btx(name)

    def try_parse_lua(self, name: str) -> Optional[Dict[str, Any]]:
        return cite.parse_lua(name, self.lua_script, self.opts)

    def try_parse_btx(self, name: str) -> Optional[Dict[str, Any]]:
        return cite.parse_btx(name, self.btx_script, self.opts)

    def try_parse_xml(self, name: str) -> Optional[Dict[str, Any]]:
        return cite.parse_xml(name)

    def try_parse_py(self, name: str) -> Optional[Dict[str, Any]]:
        with open(name, encoding="utf-8") as f:
            return ast.literal_eval(f.read())


class TestParseBibFiles(unittest.TestCase):
    def __init__(self, root: SimpleContextTestParseBibFilesCommand) -> None:
        super().__init__()
        self.root = root

    def test__equivalent_files(self, dir_: str) -> None:
        tests = group_files(os.path.join(dir_, f) for f in os.listdir(dir_))
        for test, exts in sorted(tests.items()):
            prev = None
            print("[simple_ConTeXt]   - test: {}".format(test))
            for e in exts:
                content = self.root.try_parse(e)
                if prev is not None:
                    self.assertEqual(
                        json.dumps(content, indent=2, sort_keys=True) + "\n",
                        json.dumps(prev[0], indent=2, sort_keys=True) + "\n",
                    )
                prev = (content, e)
        print("[simple_ConTeXt]   - passed bib parsing test")
