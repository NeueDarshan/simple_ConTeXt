import sublime
import sublime_plugin
import os
import re


import sys
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common


class ContextMacroSignatureEventListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands_cache = {}

    def reload_settings(self):
        common.reload_settings(self)

        name = self.current_profile_name
        if name not in self.commands_cache:
            self.commands_cache[name] = {
                "commands": common.load_commands(
                    os.path.join(
                        os.path.abspath(os.path.dirname(__file__)),
                        "interface"),
                    self.current_profile.get(
                        "command_popups", {}).get("version", "Minimals"))
            }
            self.commands_cache[name]["command_names"] = sorted(
                self.commands_cache[name]["commands"].keys())
            self.commands_cache[name]["command_completions"] = [
                ["\\" + command, ""]
                for command in self.commands_cache[name]["command_names"]]

    def on_query_completions(self, view, prefix, locations):
        if not common.is_context(view):
            return

        self.reload_settings()
        return self.commands_cache.get(
            self.current_profile_name, {}).get("command_completions", [])

    def on_modified(self, view):
        self.reload_settings()

        shouldnt_show_popup = not (
            common.is_context(view) and
            self.current_profile.get("command_popups", {}).get("on")
        )
        if shouldnt_show_popup:
            return

        command_name, tail = common.last_command_in_region(
            view, sublime.Region(0, view.sel()[0].end()))
        if not (command_name and re.match(r"\A[^\S\n]*\Z", tail)):
            view.hide_popup()
            return

        if command_name in self.commands_cache.get(
                self.current_profile_name).get("command_names", []):
            view.show_popup(
                self.get_popup_text(command_name),
                location=-1,
                max_width=600,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE
            )

    def get_popup_text(self, command_name):
        style_sheet = """
            html {{
                background-color: {background_color};
            }}
            .syntax {{
                color: {syntax_color};
                font-size: 1.2em;
            }}
            .doc_string {{
                color: {doc_string_color};
                font-size: 1em;
            }}
            .files {{
                color: {file_color};
                font-size: 1em;
            }}
        """.format(
            background_color="#151515",
            syntax_color="#8ea6b7",
            doc_string_color="#956837",
            file_color="#8ea6b7")

        signatures = []
        return_ = self.commands_cache.get(
            self.current_profile_name).get("commands", {}).get(command_name)
        command, files = return_[:-1], return_[-1]

        for variation in command:
            new_signature = """
                <div class='syntax'>
                    <code>{syntax}</code>
                </div>
            """
            parts = {"syntax": common.protect_html(variation[0])}
            if len(variation[1]) > 0:
                new_signature += """
                    <br />
                    <div class='doc_string'>
                        <code>{doc_string}</code>
                    </div>
                """
                parts["doc_string"] = common.protect_html(variation[1])
            signatures.append(new_signature.format(**parts))

        full_signature = \
            "<style>{style_sheet}</style>".format(style_sheet=style_sheet) \
            + "<br />".join(signatures)

        show_files = files and \
            self.current_profile.get("command_popups", {}).get("show_files")
        if show_files:
            full_signature += """
                <br />
                <div class='files'>
                    <code>{files}</code>
                </div>
            """.format(files=common.protect_html(" ".join(files)))

        return full_signature
