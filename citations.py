import functools
import time
import re

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import scopes
from .scripts import files
from .scripts import cite


IDLE = 0

RUNNING = 1

CITATIONS = (
    r"\A(?:(?:no|use|place|(?:btx)?(?:list|text|always|hidden))?"
    r"cit(?:e|ation))\Z"
)

EXTENSIONS = ["bib", "xml", "lua"]


def is_citation_start(text):
    return text == "["


def is_citation_history(command):
    if command:
        return command[0] not in ["left_delete", "right_delete"]
    return True


def hash_dict(func):
    return lambda dict_: func(utilities.make_hashable_dict(dict_))


@hash_dict
@functools.lru_cache(maxsize=8)
def get_entries(bibliographies):
    return sorted(
        [
            tag,
            entry.get("title", "??"),
            "{}, {}".format(
                entry.get("year", "????"),
                entry.get("author", "??"),
            ),
        ]
        for v in bibliographies.values()
        for tag, entry in v.items()
    )


class SimpleContextCiteEventListener(
    utilities.LocateSettings, sublime_plugin.ViewEventListener,
):
    extensions = [""] + [".{}".format(s) for s in EXTENSIONS]
    flags = files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
    bibliographies = {}
    state = IDLE

    def is_visible(self):
        return self.is_visible_alt()

    def reload_settings_alt(self):
        self.reload_settings()
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
        self.reload_settings_alt()
        if not self.is_visible():
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
            self.get_setting("citations/on") and
            self.is_citation_command(*ctrl)
        ):
            self.do_citation()

    def is_citation_command(self, begin, end):
        name = self.view.substr(sublime.Region(begin, end)).strip()
        return re.match(CITATIONS, name)

    def do_citation(self):
        if self.state == IDLE:
            self.state == RUNNING
            regions = self.view.find_by_selector(scopes.MAYBE_CITATION)
            possible_names = [self.view.substr(r) for r in regions]
            for name in possible_names:
                self.try_parse(name)
            self.state == IDLE
        window = self.view.window()
        if window and self.bibliographies:
            self.tags = get_entries(self.bibliographies)
            window.show_quick_panel(self.tags, self.on_done)

    def on_done(self, index):
        if 0 <= index < len(self.tags):
            try:
                tag = self.tags[index][0]
                self.view.run_command(
                    "simple_context_insert_text", {"text": tag},
                )
            except IndexError:
                pass

    def try_parse(self, name):
        if name not in self.bibliographies:
            main = self.locate_file_main(name, extensions=self.extensions)
            if main:
                self.try_parse_aux(name, main)
                return
            other = self.locate_file_context(name, extensions=self.extensions)
            if other:
                self.try_parse_aux(name, other)
                return
            self.bibliographies[name] = None

    def try_parse_aux(self, name, file_):
        if name.endswith(".bib"):
            self.bibliographies[name] = self.parse_btx(file_)
        elif name.endswith(".xml"):
            self.bibliographies[name] = self.parse_xml(file_)
        elif name.endswith(".lua"):
            self.bibliographies[name] = self.parse_lua(file_)
        else:
            self.bibliographies[name] = self.parse_btx(file_)

    def parse_lua(self, name):
        return cite.parse_lua(name, self.lua_script, self.opts)

    def parse_btx(self, name):
        return cite.parse_btx(name, self.btx_script, self.opts)

    def parse_xml(self, name):
        return cite.parse_xml(name)
