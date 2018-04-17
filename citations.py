# import json

import sublime
import sublime_plugin

from .scripts import utilities
# from .scripts import scopes
from .scripts import files
from .scripts import cite


class SimpleContextTestCiteCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    flags = files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

    def reload_settings_alt(self):
        self.reload_settings()
        self.opts = self.expand_variables(
            {
                "creationflags": self.flags,
                "env": {"PATH": "$simple_context_prefixed_path"},
            },
        )
        self.lua_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_lua.lua"
        )
        self.bib_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_btx.lua"
        )

    def run(self):
        self.reload_settings_alt()

    def parse_lua(self, name):
        return cite.parse_lua(name, self.lua_script, self.opts)

    def parse_btx(self, name):
        return cite.parse_btx(name, self.lua_script, self.opts)

    def parse_xml(self, name):
        return cite.parse_xml(name)
