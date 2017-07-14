import sublime
import sublime_plugin
import html
import os
from .scripts import common
from .scripts import parsing


PACKAGE = os.path.abspath(os.path.dirname(__file__))

TEMPLATE = """
<html>
    <style>
        div.popup {{
            padding: 0.1rem;
        }}
        div.popup div.syntax {{
            color: var(--bluish);
        }}
        div.popup div.docstring {{
            color: var(--foreground);
        }}
        div.popup div.docstring u {{
            color: var(--bluish);
            text-decoration: none;
        }}
        div.popup div.docstring i {{
            color: var(--bluish);
        }}
        div.popup div.docstring b {{
            font-weight: normal;
        }}
        div.popup div.docstring s {{
            text-decoration: none;
        }}
        div.popup div.files {{
            color: var(--bluish);
        }}
    </style>
    <body id="simple-ConTeXt-pop-up">
        <div class="popup">
            {body}
        </div>
    </body>
</html>
"""


def codeify(s):
    return common.protect_html(s, ignore_tags=["u", "i", "b", "s"], init=False)


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

        sigs = []
        command = self.commands_cache.get(
            self.settings.get("pop_ups", {}).get("interface"), {}).get(
                "details", {}).get(name)
        vars_, files = parsing.rendered_command(
            name,
            command,
            break_=pop_ups.get("line_break", None),
            sort_keys=pop_ups.get("sort_keys", True),
            sort_lists=pop_ups.get("sort_lists", True)
        )

        for var in vars_:
            sigs.append('<div class="syntax">{}</div>'.format(
                codeify(html.escape(var[0], quote=False))
            ))
            if var[1]:
                sigs.append('<div class="docstring">{}</div>'.format(
                    codeify(html.escape(var[1], quote=False))
                ))
        if files and pop_ups.get("show_files"):
            sigs.append('<div class="files">{}</div>'.format(
                codeify(html.escape(" ".join(files), quote=False))
            ))

        return TEMPLATE.format(body="<br>".join(sigs))
