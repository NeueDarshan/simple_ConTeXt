import sublime
import sublime_plugin
import threading
import json
import time
import os
import re
from .scripts import utilities
from .scripts import interface_reading as reading
from .scripts import interface_writing as writing


IDLE = 0

RUNNING = 1

TEMPLATE = """
<html>
    <style>
        {style}
    </style>
    <body id="simple-ConTeXt-pop-up">
        <div class="popup">{body}</div>
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
        self.state = IDLE
        self.style = None

    def run_loader(self):
        self.state = RUNNING
        path = os.path.join(
            sublime.packages_path(), "simple_ConTeXt", "interface"
        )
        file = os.path.join(path, "commands_{}.json".format(self.name))
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            with open(file, encoding="utf-8") as f:
                j = json.load(f)
                self.commands_cache[self.name] = {
                    "details": j,
                    "commands": sorted(
                        ["\\" + command, ""] for command in j
                    ),
                }
        except FileNotFoundError:
            print("simple_ConTeXt: building interface...")
            start_time = time.time()
            self.loader = reading.InterfaceLoader()
            self.loader.load(self._path, modules=True, tolerant=True)
            with open(file, encoding="utf-8", mode="w") as f:
                json.dump(self.loader.encode(), f)
            print(
                "simple_ConTeXt: done building interface, took {:.1f}s"
                .format(time.time() - start_time)
            )
        self.state = IDLE

    def reload_settings(self):
        utilities.reload_settings(self)
        self.load_css()
        self.name = utilities.file_as_slug(self._path)
        if utilities.is_context(self.view):
            if self.name not in self.commands_cache:
                if self.state == IDLE:
                    thread = threading.Thread(target=self.run_loader)
                    thread.start()

    def load_css(self):
        if not self.style:
            with open(os.path.join(
                sublime.packages_path(), "simple_ConTeXt", "css", "pop_up.css"
            )) as f:
                self.style = \
                    re.sub(r"/\*.*?\*/", "", f.read(), flags=re.DOTALL)

    def is_visible(self):
        return utilities.is_context(self.view)

    def on_query_completions(self, prefix, locations):
        self.reload_settings()
        for l in locations:
            if (
                self.view.match_selector(
                    l, "text.tex.context - (meta.environment.math, source)"
                ) and
                utilities.last_command_in_view(self.view, end=l)
            ):
                return self.commands_cache.get(
                    self.name, {}).get("commands", [])

    def on_modified_async(self):
        self.reload_settings()
        if not self._pop_ups.get("on"):
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
        if name in self.commands_cache.get(self.name, {}).get("details", {}):
            self.view.show_popup(
                self.get_popup_text(name),
                max_width=600,
                max_height=250,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                on_navigate=self.on_navigate
            )

    def get_popup_text(self, name):
        cmd = self.commands_cache[self.name]["details"][name]
        write = writing.InterfaceWriter()
        self.pop_up, extra = write.render(
            name, cmd, pre_code=True, **self._pop_ups
        )
        if extra:
            return TEMPLATE.format(
                body=self.pop_up + "<br><br>" + extra, style=self.style
            )
        else:
            return TEMPLATE.format(body=self.pop_up, style=self.style)

    def on_navigate(self, href):
        type_, content = href[:4], href[5:]
        if type_ == "file":
            file = utilities.locate(self._path, content)
            if os.path.exists(file):
                self.view.window().open_file(file)
            else:
                msg = (
                    'Unable to locate file "{}".\n\nSearched in the TeX tree '
                    'containing "{}".'
                )
                sublime.error_message(msg.format(content, self._path))
        elif type_ == "copy":
            if content == "html":
                self.copy(utilities.html_pretty_print(self.pop_up))
            elif content == "plain":
                self.copy(utilities.html_raw_print(self.pop_up))

    def copy(self, text):
        sublime.set_clipboard(text)
        self.view.hide_popup()
        sublime.status_message("Pop-up content copied to clipboard")
