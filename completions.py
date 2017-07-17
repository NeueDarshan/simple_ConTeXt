import sublime
import sublime_plugin
import threading
import json
import time
import os
from .scripts import utilities
from .scripts import interface_reading as reading
from .scripts import interface_writing as writing


# We use a couple of HTML tags. We chose short tags because it makes the
# files/strings significantly shorter than using long descriptive names. Here
# are their meanings:
#
# \starttabulate[|rT|l|]
#   \NC c \NC control sequence \type{\...} \NC\NR
#   \NC o \NC optional argument \NC\NR
#   \NC n \NC number \NC\NR
#   \NC k \NC key, as in \type{key=value} \NC\NR
#   \NC e \NC equals, as in \type{key=value} \NC\NR
#   \NC v \NC value, as in \type{key=value} \NC\NR
#   \NC t \NC type name, e.g.\ \type{CSNAME} means a control sequence
#             name \NC\NR
#   \NC d \NC default value \NC\NR
#   \NC i \NC inherits, styles the bit of text \quote{inherits:} in
#             \type{inherits: \...} \NC\NR
# \stoptabulate
#
# I believe that, of these tags, only \type{<i>} is recognized by miniHTML. So,
# for \type{<i>}, bear in mind that it will have the default behaviour of
# italicizing things. Better would be to use another letter, but I actually
# like this style for \quote{inherits} so it's staying for now.
TEMPLATE = """
<html>
    <style>
        c {{
            color: var(--bluish);
        }}
        o {{
            font-style: italic;
        }}
        n {{
            color: var(--purplish);
        }}
        t {{
            color: var(--greenish);
        }}
        d {{
            color: var(--greenish);
        }}
        e {{
            color: var(--redish);
        }}
    </style>
    <body id="simple-ConTeXt-pop-up">
        <popup>{body}</popup>
    </body>
</html>
"""


class SimpleContextMacroSignatureEventListener(
    sublime_plugin.ViewEventListener
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands_cache = {}
        self.lock = threading.Lock()
        self.state = 0

    def run_loader(self):
        self.state = 1
        file = os.path.join(
            sublime.packages_path(),
            "simple_ConTeXt",
            "interface",
            "commands-{}.json".format(self._name)
        )
        try:
            with open(file, encoding="utf-8") as f:
                j = json.load(f)
                self.commands_cache[self._name] = {
                    "details": j["details"],
                    "commands": sorted(
                        ["\\" + command, ""] for command in j["details"]
                    ),
                    "files": j["files"]
                }
        except FileNotFoundError:
            print("simple_ConTeXt: building interface (warning: is slow) ...")
            start_time = time.time()
            self.loader = reading.InterfaceLoader()
            self.loader.load(self._path, passes=3, modules=True)
            with open(file, encoding="utf-8", mode="w") as f:
                json.dump(self.loader.encode(), f)
            print(
                "simple_ConTeXt: done building interface, took {:.1f}s"
                .format(time.time() - start_time)
            )
        self.state = 0

    def reload_settings(self):
        utilities.reload_settings(self)
        self._path = self.settings.get("path")
        if self._path in self.paths:
            self._path = self.paths[self._path]
        self._name = utilities.file_as_slug(self._path)
        if self._name not in self.commands_cache:
            if self.state == 0:
                thread = threading.Thread(target=self.run_loader)
                thread.start()

    def on_query_completions(self, prefix, locations):
        if not utilities.is_context(self.view):
            return
        self.reload_settings()
        for l in locations:
            if self.view.match_selector(
                l, "text.tex.context - (meta.environment.math, source)"
            ):
                return self.commands_cache.get(
                    self._name, {}).get("commands", [])

    def on_modified_async(self):
        if not utilities.is_context(self.view):
            return
        self.reload_settings()
        if not self.settings.get("pop_ups", {}).get("on"):
            return
        if not self.view.match_selector(
            self.view.sel()[0].end(),
            "text.tex.context - (meta.environment.math, source)"
        ):
            return

        end = self.view.sel()[0].end()
        cmd = utilities.last_command_in_view(self.view, end=end)
        if not cmd:
            self.view.hide_popup()
            return

        name = self.view.substr(cmd)[1:]
        if name in self.commands_cache.get(self._name, {}).get("details", {}):
            self.view.show_popup(
                self.get_popup_text(name),
                max_width=600,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                on_navigate=self.on_navigate
            )

    def get_popup_text(self, name):
        cmd = self.commands_cache[self._name]["details"][name]
        files = self.commands_cache[self._name]["files"]
        pop_ups = self.settings.get("pop_ups", {})
        write = writing.InterfaceWriter()
        self.pop_up, extra = write.render(
            name, cmd, files, pre_code=True, **pop_ups
        )
        if extra:
            return TEMPLATE.format(body=self.pop_up + "<br><br>" + extra)
        else:
            return TEMPLATE.format(body=self.pop_up)

    def on_navigate(self, href):
        type_, content = href[:4], href[5:]
        if type_ == "file":
            if os.path.exists(content):
                self.view.window().open_file(content)
        elif type_ == "copy":
            if content == "html":
                self.copy(utilities.html_pretty_print(self.pop_up))
            elif content == "plain":
                self.copy(utilities.html_raw_print(self.pop_up))

    def copy(self, text):
        sublime.set_clipboard(text)
        self.view.hide_popup()
        sublime.status_message("Pop-up content copied to clipboard")
