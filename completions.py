import sublime
import sublime_plugin
import os
import re


import sys
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import parsing
from scripts import common


class ContextMacroSignatureEventListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_profile = {}
        self.commands = {}
        self.reload_settings()

    def reload_settings(self):
        try:
            self.settings = sublime.load_settings(
                "ConTeXtTools.sublime-settings")
            profile_name = self.settings.get("current_profile")

            for profile in self.settings.get("profiles", {}):
                if profile.get("name") == profile_name:
                    self.current_profile = profile
                    break

            if self.current_profile.get("name") not in self.commands:
                dict_ = self.commands[self.current_profile.get("name")] = {}
                dict_["commands"] = common.load_commands(
                    os.path.join(
                        os.path.abspath(os.path.dirname(__file__)),
                        "interface"
                    ),
                    self.current_profile)
                dict_["command_names"] = sorted(dict_["commands"].keys())
                dict_["command_completions"] = [
                    ["\\{name}".format(name=name), ""]
                    for name in dict_["command_names"]
                ]
        except TypeError:
            pass

    def on_query_completions(self, view, prefix, locations):
        if not common.is_context(view):
            return

        self.reload_settings()
        return self.commands.get(
            self.current_profile.get("name"), {}).get(
                "command_completions", [])

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

        if command_name in self.commands.get(
                self.current_profile.get("name")).get("command_names", []):
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
        command = self.commands.get(
            self.current_profile.get("name")).get("commands").get(command_name)
        files = command[-1]
        for variation in command[:-1]:
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

        show_file = files and \
            self.current_profile.get("command_popups", {}).get("show_file")
        if show_file:
            full_signature += """
                <br />
                <div class='files'>
                    <code>{files}</code>
                </div>
            """.format(files=common.protect_html(" ".join(files)))

        return full_signature
