import sublime
import sublime_plugin
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "simpleConTeXt")
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


class SimpleContextMacroSignatureEventListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands_cache = {}

    def reload_settings(self):
        common.reload_settings(self)
        name = self.settings.get("pop_ups", {}).get("interface")
        if name and name not in self.commands_cache:
            try:
                details = common.load_commands(
                    os.path.join(PACKAGE, "interface"), name
                )
                if details:
                    self.commands_cache[name] = {"details": details}
                    self.commands_cache[name]["commands"] = sorted(
                        ["\\" + command, ""]
                        for command in self.commands_cache[name]["details"]
                    )
            except FileNotFoundError as e:
                print(e)

    def on_query_completions(self, view, prefix, locations):
        if not common.is_context(view):
            return

        self.reload_settings()
        for l in locations:
            if view.match_selector(
                l, "text.tex.context - (meta.environment.math, source)"
            ):
                return self.commands_cache.get(
                    self.settings.get("pop_ups", {}).get(
                        "interface"), {}).get("commands", [])

    def on_modified_async(self, view):
        if not common.is_context(view):
            return

        self.reload_settings()
        if not self.settings.get("pop_ups", {}).get("on"):
            return

        if not view.match_selector(
            view.sel()[0].end(),
            "text.tex.context - (meta.environment.math, source)"
        ):
            return

        end = view.sel()[0].end()
        cmd = common.last_command_in_view(view, end=end)
        if not cmd:
            view.hide_popup()
            return

        name = view.substr(cmd)[1:]
        if name in self.commands_cache.get(
            self.settings.get("pop_ups", {}).get(
                "interface"), {}).get("details", {}):
            view.show_popup(
                self.get_popup_text(name),
                max_width=600,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE
            )

    def get_popup_text(self, name):
        pop_ups = self.settings.get("pop_ups", {})
        colours = self.colour_schemes.get(pop_ups.get("colour_scheme"), {})
        style = STYLE_SHEET.format(
            background=colours.get("background"),
            syntax=colours.get("primary"),
            doc_string=colours.get("secondary"),
            file=colours.get("primary")
        )

        signatures = []
        command = self.commands_cache.get(
            self.settings.get("pop_ups", {}).get("interface"), {}).get(
                "details", {}).get(name)
        variations, files = parsing.rendered_command(
            name,
            command,
            break_=pop_ups.get("line_break", None),
            sort_keys=pop_ups.get("sort_keys", True),
            sort_lists=pop_ups.get("sort_lists", True)
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

        if files and pop_ups.get("show_files"):
            full_signature += """
                <br />
                <div class='files'>
                    <code>{}</code>
                </div>
            """.format(common.protect_html(" ".join(files)))

        return full_signature
