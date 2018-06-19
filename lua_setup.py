import sublime
import sublime_plugin

from .scripts import utilities


LUA_SCRIPTS = (
    "scripts/{}.lua".format(name)
    for name in ("parse_btx", "parse_log", "parse_lua", "table_to_dict")
)


class SimpleContextUnpackLuaScriptsCommand(sublime_plugin.WindowCommand):
    first = True

    def run(self, force=False, **kwargs):
        if force:
            self.run_main()
        elif self.first:
            self.run_main()
            self.first = False

    def run_main(self):
        self.window.run_command("simple_context_unpack_lua_scripts_internal")


class SimpleContextUnpackLuaScriptsInternalCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    def run(self):
        self.reload_settings()
        for script in LUA_SCRIPTS:
            print("Packages/simple_ConTeXt/{}".format(script))
            content = sublime.load_resource(
                "Packages/simple_ConTeXt/{}".format(script)
            )
            # Better would probably be to produce hashes to see whether the
            # source file has changed: if so, only then write to the target
            # file.
            with open(
                self.expand_variables(
                    "${packages}/simple_ConTeXt/%s" % script
                ),
                mode="w",
            ) as f:
                f.write(content)
