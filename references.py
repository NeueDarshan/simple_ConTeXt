import sublime
import sublime_plugin
import re
from .scripts import utilities
from .scripts import scopes


BUILT_IN_REFERENCERS = r"(about|in|at)"


class SimpleContextReferenceEventListener(
    sublime_plugin.ViewEventListener
):
    def reload_settings(self):
        utilities.reload_settings(self)

    def is_visible(self):
        return scopes.is_context(self.view)

    def on_modified_async(self):
        self.reload_settings()
        if not (self.is_visible() and self._references.get("on")):
            return

        sel = self.view.sel()
        if len(sel) == 0:
            return
        else:
            region = sel[0]

        ctrl = scopes.last_block_in_region(
            self.view,
            0,
            region.begin(),
            scopes.CONTROL_SEQ,
            skip=scopes.SKIP_ARGS_AND_SPACES
        )
        if ctrl:
            last_char = self.view.substr(max(0, region.end() - 1))
            last_cmd = self.view.command_history(0, modifying_only=True)
            if (
                self.is_reference_start(last_char) and
                self.is_reference_history(last_cmd) and
                self.is_reference_command(*ctrl)
            ):
                self.view.window().run_command(
                    "simple_context_show_overlay",
                    {
                        "scope": "reference",
                        "on_choose": "insert",
                        "selected_index": "closest",
                    }
                )

    def is_reference_start(self, text):
        return text == "["

    def is_reference_history(self, command):
        return command[0] not in ["left_delete", "right_delete"]

    def is_reference_command(self, begin, end):
        name = self.view.substr(sublime.Region(begin, end))
        return re.match(BUILT_IN_REFERENCERS, name)
