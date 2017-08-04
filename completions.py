import sublime
import sublime_plugin
import collections
import threading
import random
import json
import os
import re
from .scripts import utilities
from .scripts import save
from .scripts import load


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


class LruCache:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = collections.OrderedDict()

    def __setitem__(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key, last=False)
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=True)

    def __getitem__(self, key):
        return self.cache[key]

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)


class VirtualCommandDict:
    def __init__(
        self, dir_, cmds="_commands.json", max_size=100, local_size=10
    ):
        self.dir = dir_
        self.missing = sorted(f for f in os.listdir(self.dir) if f != cmds)
        with open(os.path.join(self.dir, cmds)) as f:
            self.keys = set(json.load(f))
        self.max_size = max_size
        self.local_size = local_size
        self.store = collections.OrderedDict()

    def __setitem__(self, key, value):
        self.keys.add(key)
        self.store[key] = value
        self.store.move_to_end(key, last=False)
        while len(self.store) > self.max_size:
            self.store.popitem(last=True)

    def __getitem__(self, key):
        if key in self.keys:
            if key in self.store:
                return self.store[key]
            else:
                name = min(f for f in self.missing if key <= f)
                with open(os.path.join(self.dir, name)) as f:
                    data = json.load(f)
                while len(self.store) + self.local_size > self.max_size:
                    self.store.popitem(last=True)
                for k in random.sample(list(data), self.local_size):
                    self.keys.add(k)
                    self.store[k] = data[k]
                    self.store.move_to_end(k, last=True)
                self[key] = data[key]
                return self[key]
        else:
            raise KeyError

    def __len__(self):
        return len(self.store)

    def __contains__(self, key):
        return key in self.keys


class SimpleContextMacroSignatureEventListener(
    sublime_plugin.ViewEventListener
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.html_cache = {}
        self.lock = threading.Lock()
        self.loader = load.InterfaceLoader()
        self.state = IDLE
        self.style = None
        self.file_min = 20000
        self.scope_sel = "text.tex.context - (meta.environment.math, source)"

    def reload_settings(self):
        utilities.reload_settings(self)
        self.load_css()
        self.name = utilities.file_as_slug(self._path)
        if (
            self.state == IDLE and
            self.is_visible() and
            self.name not in self.cache
        ):
            self.state = RUNNING
            thread = threading.Thread(target=self.reload_settings_aux)
            thread.start()

    def load_css(self):
        if not self.style:
            self.style = re.sub(
                r"/\*.*?\*/",
                r"",
                sublime.load_resource(
                    "Packages/simple_ConTeXt/css/pop_up.css"
                ),
                flags=re.DOTALL
            )

    def reload_settings_aux(self):
        self.interface_path = os.path.join(
            sublime.packages_path(), "simple_ConTeXt", "interface", self.name
        )
        if not os.path.exists(self.interface_path):
            os.makedirs(os.path.join(self.interface_path))
        commands = os.path.join(self.interface_path, "_commands.json")
        if not os.path.exists(commands):
            self.save_interface()
        self.load_commands()
        self.state = IDLE

    def save_interface(self):
        saver = save.InterfaceSaver()
        saver.save(self._path, modules=True, tolerant=True)
        cmds = saver.encode()
        cache, key, size = {}, None, 0
        for name in sorted(cmds):
            key = name
            val = cmds[key]
            size += len(str(val))
            cache[key] = val
            if size > self.file_cap:
                file = os.path.join(self.interface_path, "{}.json".format(key))
                with open(file, encoding="utf-8", mode="w") as f:
                    json.dump(cache, f)
                cache.clear()
                size = 0
        if cache:
            file = os.path.join(self.interface_path, "{}.json".format(key))
            with open(file, encoding="utf-8", mode="w") as f:
                json.dump(cache, f)
        file = os.path.join(self.interface_path, "_commands.json")
        with open(file, encoding="utf-8", mode="w") as f:
            json.dump(sorted(cmds), f)

    def load_commands(self):
        self.cache[self.name] = VirtualCommandDict(
            self.interface_path, max_size=500, local_size=25
        )
        self.html_cache[self.name] = LruCache(max_size=500)

    def is_visible(self):
        return utilities.is_context(self.view)

    def on_query_completions(self, prefix, locations):
        self.reload_settings()
        if self.state == IDLE:
            for l in locations:
                if (
                    self.view.match_selector(l, self.scope_sel) and
                    utilities.last_command_in_view(self.view, end=l)
                ):
                    return [
                        ["\\" + cmd, ""] for cmd in self.cache[self.name].keys
                    ]

    def on_modified_async(self):
        self.reload_settings()
        end = self.view.sel()[0].end()
        if not (
            self.state == IDLE and
            self.is_visible() and
            self._pop_ups.get("on") and
            self.view.match_selector(end, self.scope_sel)
        ):
            self.view.hide_popup()
            return

        cmd = utilities.last_command_in_view(
            self.view, end=end, skip=utilities.skip_nothing
        )
        if not cmd:
            self.view.hide_popup()
            return

        name = self.view.substr(cmd)[1:]
        if name in self.cache[self.name]:
            self.view.show_popup(
                self.get_popup_text(name),
                max_width=600,
                max_height=250,
                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                on_navigate=self.on_navigate
            )
        else:
            self.view.hide_popup()

    def get_popup_text(self, name):
        new_pop_up_state = json.dumps(self._pop_ups, sort_keys=True)
        if not hasattr(self, "prev_pop_up_state"):
            self.prev_pop_up_state = ""
        if not (
            name in self.html_cache[self.name] and
            new_pop_up_state == self.prev_pop_up_state
        ):
            cmd = self.cache[self.name][name]
            self.pop_up, extra = self.loader.load(
                name, cmd, pre_code=True, **self._pop_ups
            )
            self.html_cache[self.name][name] = self.pop_up
            if extra:
                self.html_cache[self.name][name] += "<br><br>" + extra
        self.prev_pop_up_state = new_pop_up_state
        return TEMPLATE.format(
            body=self.html_cache[self.name][name], style=self.style
        )

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
        self.view.hide_popup()
        sublime.set_clipboard(text)
        sublime.status_message("Pop-up content copied to clipboard")
