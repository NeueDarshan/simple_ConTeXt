import functools
import threading
import re

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import scopes
from .scripts import files
from .scripts import cite


CITATIONS = (
    r"\A(?:(?:no|use|place|(?:btx)?(?:list|text|always|hidden))?"
    r"cit(?:e|ation))\Z"
)

EXTENSIONS = ("bib", "xml", "lua")

FORMAT = cite.DefaultFormatter(
    handler=lambda k: "????" if k == "year" else "??"
)


def is_citation_start(text):
    return text == "["


def is_citation_history(cmd):
    return cmd[0] not in ("left_delete", "right_delete") if cmd else True


@utilities.hash_first_arg
@functools.lru_cache(maxsize=128)
def get_entries(bibliographies, format_str):
    return sorted(
        [
            (
                tag,
                [
                    FORMAT.format(s, tag=tag, **entry)
                    for s in format_str.split("<>")
                ],
            )
            for tag, entry in bibliographies.items()
        ],
        key=lambda tup: tup[1][0],
    )


class SimpleContextCiteEventListener(
    utilities.LocateSettings, sublime_plugin.ViewEventListener,
):
    extensions = ("",) + tuple(".{}".format(s) for s in EXTENSIONS)
    flags = files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
    bibliographies = {}
    bib_per_files = {}
    lock = threading.Lock()

    def is_visible(self):
        return self.is_visible_alt()

    def reload_settings(self):
        super().reload_settings()
        self.file_name = self.view.file_name()
        self.opts = self.expand_variables(
            {
                "creationflags": self.flags,
                "env": {"PATH": "$simple_context_prefixed_path"},
            }
        )
        self.lua_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_lua.lua"
        )
        self.btx_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_btx.lua"
        )

    def on_modified_async(self):
        self.reload_settings()
        format_str = self.get_setting("citations/format")
        if not (
            self.is_visible() and
            self.get_setting("citations/on") and
            format_str
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
                target=lambda: self.do_citation(self.file_name, format_str)
            ).start()

    def is_citation_command(self, begin, end):
        name = self.view.substr(sublime.Region(begin, end)).strip()
        return re.match(CITATIONS, name)

    def do_citation(self, view_name, format_str):
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
                    if extra:
                        dict_.update(extra)
            self.tags = get_entries(dict_, format_str)
            window.show_quick_panel(
                [tup[1] for tup in self.tags], self.on_done,
            )

    def on_done(self, index):
        if 0 <= index < len(self.tags):
            text = self.tags[index]
            if text:
                self.view.run_command(
                    "simple_context_insert_text", {"text": text[0]},
                )

    def try_parse(self, name, view_name):
        if view_name:
            self.bib_per_files.setdefault(view_name, {})
        if name not in self.bib_per_files[view_name]:
            if view_name:
                main = self.locate_file_main(name, extensions=self.extensions)
                if main:
                    self.bib_per_files[view_name][name] = main
                    self.bibliographies[main] = self.try_parse_aux(name, main)
                    return
            other = self.locate_file_context(name, extensions=self.extensions)
            if other:
                self.bib_per_files[view_name][name] = other
                self.bibliographies[other] = self.try_parse_aux(name, other)
                return
            self.bib_per_files[view_name][name] = 0

    def try_parse_aux(self, name, file_):
        if name.endswith(".bib"):
            return self.parse_btx(file_)
        elif name.endswith(".xml"):
            return self.parse_xml(file_)
        elif name.endswith(".lua"):
            return self.parse_lua(file_)
        return self.parse_btx(file_)

    def parse_lua(self, name):
        return cite.parse_lua(name, self.lua_script, self.opts)

    def parse_btx(self, name):
        return cite.parse_btx(name, self.btx_script, self.opts)

    def parse_xml(self, name):
        return cite.parse_xml(name)
