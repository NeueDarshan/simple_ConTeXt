import sublime
import sublime_plugin
import collections
import threading
import string
import json
import os
from .scripts import utilities
from .scripts import html_css
from .scripts import scopes
from .scripts import files
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
        <div class="outer">
            <div class="inner">
                <div class="popup">{body}</div>
            </div>
        </div>
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
        self.cache = collections.OrderedDict()

    def __setitem__(self, key, value):
        self.keys.add(key)
        self.cache[key] = value
        self.cache.move_to_end(key, last=False)
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=True)

    def __getitem__(self, key):
        if key in self.keys:
            if key in self.cache:
                return self.cache[key]
            else:
                name = min(f for f in self.missing if key <= f)
                with open(os.path.join(self.dir, name)) as f:
                    data = json.load(f)
                while len(self.cache) + self.local_size > self.max_size:
                    self.cache.popitem(last=True)
                for k in utilities.safe_random_sample(
                    list(data), self.local_size
                ):
                    self.keys.add(k)
                    self.cache[k] = data[k]
                    self.cache.move_to_end(k, last=True)
                self[key] = data[key]
                return self[key]
        else:
            raise KeyError

    def __len__(self):
        return len(self.cache)

    def __contains__(self, key):
        return key in self.keys

    def get_keys(self):
        return sorted(self.keys)


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
        self.file_min = 20000
        self.param_char = string.ascii_letters  # + string.whitespace
        exts = ["tex"] + [
            "mk{}".format(s) for s in ["ii", "iv", "vi", "ix", "xi"]
        ]
        self.extensions = [".{}".format(s) for s in exts]

    def reload_settings(self):
        utilities.reload_settings(self)
        self.flags = \
            files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self.load_css()
        self.name = files.file_as_slug(self._path)
        if (
            self.state == IDLE and
            self.is_visible() and
            self.name not in self.cache
        ):
            self.state = RUNNING
            thread = threading.Thread(target=self.reload_settings_aux)
            thread.start()

    def load_css(self):
        if not hasattr(self, "style"):
            self.style = html_css.strip_css_comments(
                sublime.load_resource(
                    "Packages/simple_ConTeXt/css/pop_up.css"
                )
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
        saver = save.InterfaceSaver(flags=self.flags)
        saver.save(self._path, modules=True, tolerant=True)
        cmds = saver.encode()
        cache, key, size = {}, None, 0
        for name in sorted(cmds):
            key = name
            val = cmds[key]
            size += len(str(val))
            cache[key] = val
            if size > self.file_min:
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
        if self.state != IDLE or not self.is_visible():
            return

        for location in locations:
            if scopes.enclosing_block(
                self.view, location - 1, scopes.FULL_CONTROL_SEQ
            ):
                return [
                    ["\\" + ctrl, ""]
                    for ctrl in self.cache[self.name].get_keys()
                ]

    def on_hover(self, point, hover_zone):
        self.reload_settings()
        if (
            self.state != IDLE or
            hover_zone != sublime.HOVER_TEXT or
            not self._pop_ups.get("methods", {}).get("on_hover") or
            not self.is_visible()
        ):
            self.view.hide_popup()
            return

        ctrl = scopes.enclosing_block(self.view, point, scopes.CONTROL_WORD)
        if not ctrl:
            return
        name = self.view.substr(sublime.Region(*ctrl))
        if name in self.cache.get(self.name, {}):
            self.view.show_popup(
                self.get_popup_text(name),
                location=ctrl[0],
                max_width=600,
                max_height=250,
                flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                on_navigate=self.on_navigate,
            )
        else:
            self.view.hide_popup()

    def on_modified_async(self):
        self.reload_settings()
        if (
            self.state != IDLE or
            not self.is_visible() or
            not self._pop_ups.get("methods", {}).get("auto_complete")
        ):
            self.view.hide_popup()
            return

        for sel in self.view.sel():
            ctrl = scopes.left_enclosing_block(
                self.view, sel.end() - 1, scopes.CONTROL_SEQ
            )
            if not ctrl:
                self.view.hide_popup()
                continue
            name = self.view.substr(sublime.Region(*ctrl))
            if name in self.cache.get(self.name, {}):
                self.view.show_popup(
                    self.get_popup_text(name),
                    location=ctrl[0],
                    max_width=600,
                    max_height=250,
                    flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                    on_navigate=self.on_navigate,
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
                name, cmd, protect_space=True, **self._pop_ups
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
            self.on_navigate_file(content)
        elif type_ == "copy":
            if content == "html":
                self.copy(html_css.pretty_print(self.pop_up))
            elif content == "plain":
                self.copy(html_css.raw_print(self.pop_up))

    def on_navigate_file(self, name):
        main = files.locate(self._path, name, flags=self.flags)
        if main and os.path.exists(main):
            self.view.window().open_file(main)
        else:
            other = files.fuzzy_locate(
                self._path, name, extensions=self.extensions, flags=self.flags
            )
            if other and os.path.exists(other):
                #D For some reason, this is crashing Sublime Text on finishing
                #D the dialogue \periods.
                # msg = (
                #     'Unable to locate file "{}".\n\nSearched in the TeX tree '
                #     'containing "{}".\n\nFound file "{}" with similar name, '
                #     'open instead?'
                # ).format(name, self._path, os.path.basename(other))
                # if sublime.ok_cancel_dialog(msg):
                #     self.view.window().open_file(other)
                #D So instead let's just open the file.
                self.view.window().open_file(other)
            else:
                msg = (
                    'Unable to locate file "{}".\n\nSearched in the TeX tree '
                    'containing "{}".'
                )
                sublime.error_message(msg.format(name, self._path))

    def copy(self, text):
        self.view.hide_popup()
        sublime.set_clipboard(text)
        sublime.status_message("Pop-up content copied to clipboard")
