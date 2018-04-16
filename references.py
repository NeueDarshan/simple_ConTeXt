import re

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import scopes


BUFFER = "meta.buffer-name.context"

BUILT_IN_REFERENCERS = r"\A(about|in|at|from|over)\Z"

BUILT_IN_BUFFERS = [
    "ctxluabuffer",
    "getbuffer",
    "savebuffer",
    "typebuffer",
    "typesetbuffer",
    "setupbuffer",
    "scitebuffer",
    "getbufferdata",
    "getdefinedbuffer",
    "inlinebuffer",
    "mkvibuffer",
    "processTEXbuffer",
    "resetbuffer",
]


def is_reference_start(text):
    return text == "["


def is_reference_history(command):
    if command:
        return command[0] not in ["left_delete", "right_delete"]
    return True


class SimpleContextReferenceEventListener(sublime_plugin.ViewEventListener):
    def reload_settings(self):
        utilities.reload_settings(self)

    def get_setting(self, opt):
        return utilities.get_setting(self, opt)

    def is_visible(self):
        return scopes.is_context(self.view)

    def on_modified_async(self):
        self.reload_settings()
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
            not is_reference_start(last_char) or
            not is_reference_history(last_cmd)
        ):
            return

        if (
            self.get_setting("references/on") and
            self.is_reference_command(*ctrl)
        ):
            self.do_reference()
        elif (
            self.get_setting("buffer/on") and
            self.is_buffer_command(*ctrl)
        ):
            self.do_buffer()

    def do_reference(self):
        self.view.window().run_command(
            "simple_context_show_overlay",
            {
                "selector": "reference",
                "on_choose": "insert",
                "selected_index": "closest",
            },
        )

    def do_buffer(self):
        self.view.window().run_command(
            "simple_context_show_overlay",
            {
                "selector_raw": BUFFER,
                "on_choose": "insert",
                "selected_index": "closest",
            },
        )

    def is_reference_command(self, begin, end):
        name = self.view.substr(sublime.Region(begin, end))
        user_regex = self.get_setting("references/command_regex")
        if re.match(BUILT_IN_REFERENCERS, name):
            return True
        elif user_regex and re.match(r"\A" + user_regex + r"\Z", name):
            return True
        return False

    def is_buffer_command(self, begin, end):
        name = self.view.substr(sublime.Region(begin, end))
        return name in BUILT_IN_BUFFERS
