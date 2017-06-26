import sublime
import sublime_plugin
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
from scripts import common
from scripts import parsing


STYLE_SHEET = """
html {{
    background-color: {background};
}}
.syntax {{
    color: {syntax};
    font-size: 1.1em;
}}
.doc_string {{
    color: {doc_string};
    font-size: 1em;
}}
.files {{
    color: {file};
    font-size: 1em;
}}
code {{
    font-family: monospace;
}}
"""


class ContextMacroSignatureEventListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands_cache = {}

    def reload_settings(self):
        common.reload_settings(self)
        name = self.current_interface_name
        if name not in self.commands_cache:
            try:
                path = os.path.join(PACKAGE, "interface")
                self.commands_cache[name] = {
                    "details": common.load_commands(path, name)
                }
                self.commands_cache[name]["commands"] = sorted([
                    ["\\" + command, ""]
                    for command in self.commands_cache[name]["details"]
                ])
            except FileNotFoundError as e:
                pass

    def on_query_completions(self, view, prefix, locations):
        if not common.is_context(view):
            return

        self.reload_settings()
        return self.commands_cache.get(
            self.current_interface_name, {}).get("commands", [])

    def on_modified(self, view):
        if not common.is_context(view):
            return

        self.reload_settings()
        if not self.current_profile.get("command_popups", {}).get("on"):
            return

        end = view.sel()[0].end()
        cmd = common.last_command_in_view(view, end=end)
        if not cmd:
            view.hide_popup()
            return

        name = view.substr(cmd)[1:]
        if name in self.commands_cache.get(
                self.current_interface_name, {}).get("details", {}):
            view.show_popup(
                self.get_popup_text(name),
                location=-1,
                max_width=600,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE
            )

    def get_popup_text(self, name):
        visuals = self.current_profile.get(
            "command_popups", {}).get("visuals", {})
        colors = visuals.get("colors", {})
        style = STYLE_SHEET.format(
            background=colors.get("background", "rgb(46, 47, 41)"),
            syntax=colors.get("primary", "rgb(36, 151, 227)"),
            doc_string=colors.get("secondary", "rgb(151, 151, 148)"),
            file=colors.get("primary", "rgb(36, 151, 227)")
        )

        signatures = []
        command = self.commands_cache.get(
            self.current_interface_name, {}).get("details", {}).get(name)
        variations, files = parsing.rendered_command(
            name,
            command,
            break_=visuals.get("line_break", None),
            sort_keys=visuals.get("sort_keys", True),
            sort_lists=visuals.get("sort_lists", True)
        )

        for variation in variations:
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

        full_signature = "<style>{}</style>".format(style) + \
            "<br />".join(signatures)

        show_files = files and \
            self.current_profile.get("command_popups", {}).get("show_files")
        if show_files:
            full_signature += """
                <br />
                <div class='files'>
                    <code>{}</code>
                </div>
            """.format(common.protect_html(" ".join(files)))

        return full_signature
