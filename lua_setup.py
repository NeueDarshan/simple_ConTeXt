import os

import sublime
import sublime_plugin

from .scripts import utilities


LOCATION = os.path.join("simple_ConTeXt", "scripts")

LUA_SCRIPTS = (
    "{}.lua".format(name) for name in {
        "parse_btx", "parse_log", "parse_lua", "table_to_dict",
    }
)


class SimpleContextUnpackLuaScriptsCommand(sublime_plugin.WindowCommand):
    first = True

    def run(self, force: bool = False, **kwargs) -> None:
        if force:
            self.run_main()
        elif self.first:
            self.run_main()
            self.first = False

    def run_main(self) -> None:
        self.window.run_command("simple_context_unpack_lua_scripts_internal")


class SimpleContextUnpackLuaScriptsInternalCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    def run(self) -> None:
        self.reload_settings()
        location = os.path.join(
            self.expand_variables("${packages}"), LOCATION,
        )
        if not os.path.exists(location):
            os.makedirs(location)
        for script in LUA_SCRIPTS:
            # The format that `sublime.load_resource` expects seems to be with
            # a forward slash, so we set that up.
            content = sublime.load_resource(
                os.path.join(
                    "Packages", LOCATION, script,
                ).replace(os.path.sep, "/")
            ).replace("\r\n", "\n").replace("\r", "\n")
            # Better would probably be to produce hashes to see whether the
            # source file has changed: if so, only then write to the target
            # file.
            with open(
                os.path.join(location, script), encoding="utf-8", mode="w",
            ) as f:
                f.write(content)
