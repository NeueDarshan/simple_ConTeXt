import sublime
import sublime_plugin
import collections
import threading
import string
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
        self.style = None
        self.file_min = 20000
        self.cmd_scope = "text.tex.context - (meta.environment.math, source)"
        self.param_scope = (
            "text.tex.context meta.brackets.context - "
            "(comment.line.percentage.context, meta.other.value.context, "
            "punctuation.separator.comma.context, "
            "keyword.operator.assignment.context)"
        )
        self.param_char = string.ascii_letters  # + string.whitespace
        self.extensions = ["tex", "mkii", "mkiv", "mkvi", "mkix", "mkxi"]

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

    def fetch_keys(self, command):
        data = self.cache[self.name][command]
        for var in data:
            con = var.get("con")
            if con:
                for arg in con:
                    if isinstance(arg, dict):
                        desc = arg.get("con")
                        if isinstance(desc, dict):
                            return [
                                utilities.html_strip_tags(k).lower()
                                for k in desc.keys()
                            ]
                        # elif isinstance(desc, list):
                        #     return desc

    def on_query_completions(self, prefix, locations):
        self.reload_settings()
        if not self.is_visible():
            return
        if self.state == IDLE:
            for l in locations:
                cmd = utilities.last_command_in_view(
                    self.view,
                    begin=None,
                    end=l,
                    skip=utilities.skip_args
                )
                if (
                    cmd and
                    self.view.match_selector(l - 1, self.param_scope) and
                    self.view.substr(l - 1) in self.param_char
                ):
                    cs = self.view.substr(cmd)[1:]
                    keys = self.fetch_keys(cs)
                    if keys:
                        return [[s, "{}=$1,$0".format(s)] for s in keys]
                elif (
                    self.view.match_selector(l, self.cmd_scope) and
                    utilities.last_command_in_view(
                        self.view, end=l, skip=utilities.skip_nothing
                    )
                ):
                    return [
                        ["\\" + cs, ""]
                        for cs in self.cache[self.name].get_keys()
                    ]

    def on_modified_async(self):
        self.reload_settings()
        if not (
            self.state == IDLE and
            self.is_visible()
        ):
            self.view.hide_popup()
            return

        end = self.view.sel()[0].end()
        cmd = utilities.last_command_in_view(
            self.view, end=end, skip=utilities.skip_nothing
        )

        if (
            not cmd and
            self.view.match_selector(end, self.param_scope) and
            utilities.last_command_in_view(
                self.view, begin=None, end=end, skip=utilities.skip_args
            )
        ):
            self.view.hide_popup()
            self.view.run_command(
                "auto_complete",
                {"disable_auto_insert": True, "api_completions_only": True}
            )
            return

        if not (
            self._pop_ups.get("on") and
            self.view.match_selector(end, self.cmd_scope) and
            cmd
        ):
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
            self.on_navigate_file(content)
        elif type_ == "copy":
            if content == "html":
                self.copy(utilities.html_pretty_print(self.pop_up))
            elif content == "plain":
                self.copy(utilities.html_raw_print(self.pop_up))

    def on_navigate_file(self, name):
        main = utilities.locate(self._path, name)
        if main and os.path.exists(main):
            self.view.window().open_file(main)
        else:
            other = utilities.fuzzy_locate(
                self._path, name, extensions=self.extensions
            )
            if other and os.path.exists(other):
                # # For some reason, this is crashing ST on finishing the
                # # dialogue \periods
                # msg = (
                #     'Unable to locate file "{}".\n\nSearched in the TeX tree '
                #     'containing "{}".\n\nFound file "{}" with similar name, '
                #     'open instead?'
                # ).format(name, self._path, os.path.basename(other))
                # if sublime.ok_cancel_dialog(msg):
                #     self.view.window().open_file(other)
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
