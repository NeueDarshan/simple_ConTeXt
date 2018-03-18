import threading
import string
import json
import os

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import randomize
from .scripts import html_css
from .scripts import scopes
from .scripts import files
from .scripts import load


IDLE = 0

RUNNING = 1

TEMPLATE = """
<html>
    <style>
        {extra_style}
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


def extra_style():
    result = []
    suffixes = ["style", "weight", "color", "background"]
    data = {
        "con": "",
        "flo": "flow",
        "mod": "modifier",
        "sto": "storage",
        "lan": "language",
    }
    aux = {
        "pun": "delimiter",
        "key": "key",
        "equ": "equals",
        "num": "numeric",
        "com": "comma"
    }

    for tag, pre in data.items():
        for suf in suffixes:
            for opt in ["", "slash"]:
                result.append(
                    "--%s%scontrol-sequence-%s: {%s_%s};" % (
                        opt + "-" if opt else "",
                        pre + "-" if pre else "",
                        suf,
                        "s{:.2}".format(tag) if opt else tag,
                        suf
                    )
                )

    for tag, pre in aux.items():
        for suf in suffixes:
            result.append("--%s-%s: {%s_%s};" % (pre, suf, tag, suf))

    return "html {{%s}}" % "\n".join(result)


EXTRA_STYLE = extra_style()


class VirtualCommandDict:
    def __init__(
        self, dir_, max_size=100, local_size=10, cmds="_commands.json"
    ):
        self.dir = dir_
        self.missing = sorted(f for f in os.listdir(self.dir) if f != cmds)
        with open(os.path.join(self.dir, cmds)) as f:
            self.cmds = set(json.load(f))
        self.local_size = local_size
        self.cache = utilities.FuzzyOrderedDict(max_size=max_size)

    def __setitem__(self, key, value):
        self.cmds.add(key)
        self.cache.add_left(key, value)

    def __getitem__(self, key):
        if key in self.cmds:
            if key in self.cache:
                return self.cache[key]
            name = min(f for f in self.missing if key <= f)
            with open(os.path.join(self.dir, name)) as f:
                data = json.load(f)

            sample = [
                (k, data[k])
                for k in randomize.safe_random_sample(
                    list(data), self.local_size
                )
            ]
            self.cache.fuzzy_add_right(sample)
            for k, _ in sample:
                self.cmds.add(k)

            self[key] = data[key]
            return self[key]
        else:
            raise KeyError

    def __len__(self):
        return len(self.cache)

    def __contains__(self, key):
        return key in self.cmds

    def get_cmds(self):
        return sorted(self.cmds)


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
        self.extensions = [".mkix", ".mkxi", ".mkiv", ".mkvi", ".tex", ".mkii"]

    def reload_settings(self):
        utilities.reload_settings(self)
        self.flags = \
            files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self.name = files.file_as_slug(self._path)
        self.size = self.view.size()
        if (
            self.state == IDLE and
            self.is_visible() and
            self.name not in self.cache
        ):
            self.state = RUNNING
            thread = threading.Thread(target=self.reload_settings_aux)
            thread.start()

    def reload_settings_aux(self):
        self.view.window().run_command(
            "simple_context_regenerate_interface_files",
            {
                "do_all": False,
                "paths": [self._path],
                "overwrite": False,
            }
        )
        self.load_commands(
            os.path.join(
                sublime.packages_path(),
                "simple_ConTeXt",
                "interface",
                self.name
            )
        )
        self.state = IDLE

    def load_css(self):
        self.style = html_css.strip_css_comments(
            sublime.load_resource(
                "Packages/simple_ConTeXt/css/pop_up.css"
            )
        )

    def load_commands(self, path):
        try:
            self.cache[self.name] = \
                VirtualCommandDict(path, max_size=500, local_size=25)
            self.html_cache[self.name] = \
                utilities.LeastRecentlyUsedCache(max_size=500)
        except OSError:
            pass

    def is_visible(self):
        return scopes.is_context(self.view)

    def on_query_completions(self, prefix, locations):
        self.reload_settings()
        if self.state != IDLE or not self.is_visible():
            return None

        for location in locations:
            if scopes.enclosing_block(
                self.view, location-1, scopes.FULL_CONTROL_SEQ, end=self.size
            ):
                return [
                    ["\\" + ctrl, ""]
                    for ctrl in self.cache[self.name].get_cmds()
                ]
        return None

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

        ctrl = scopes.enclosing_block(
            self.view, point, scopes.CONTROL_WORD, end=self.size
        )
        if not ctrl:
            return
        name = self.view.substr(sublime.Region(*ctrl))
        if name in self.cache.get(self.name, {}):
            self.view.show_popup(
                self.get_popup_text(name),
                location=ctrl[0] - 1,
                max_width=600,
                flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                on_navigate=self.on_navigate
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
            end = sel.end()
            if end < self.size:
                end -= 1
            ctrl = scopes.left_enclosing_block(
                self.view, end, scopes.CONTROL_SEQ, end=self.size
            )
            if not ctrl:
                self.view.hide_popup()
                continue
            name = self.view.substr(sublime.Region(*ctrl))
            if name in self.cache.get(self.name, {}):
                self.view.show_popup(
                    self.get_popup_text(name),
                    location=ctrl[0] - 1,
                    max_width=600,
                    flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                    on_navigate=self.on_navigate
                )
                return
            else:
                self.view.hide_popup()

    def get_popup_text(self, name):
        new_pop_up_state = json.dumps(self._pop_ups, sort_keys=True)
        if not hasattr(self, "prev_pop_up_state"):
            self.prev_pop_up_state = None
        if new_pop_up_state != self.prev_pop_up_state:
            self.html_cache[self.name].clear()
        if name not in self.html_cache[self.name]:
            cmd = self.cache[self.name][name]
            self.html_cache[self.name][name] = self.loader.load(
                name, cmd, protect_space=True, **self._pop_ups
            )
        self.prev_pop_up_state = new_pop_up_state
        self.popup_name = name

        self.load_css()
        return TEMPLATE.format(
            body="<br><br>".join(
                s for s in self.html_cache[self.name][name] if s
            ),
            style=self.style,
            extra_style=self.get_extra_style(),
        )

    def get_extra_style(self):
        con, sco = self.styles_for_scope("support.function")
        flo, sfl = self.styles_for_scope("keyword.control")
        mod, smo = self.styles_for_scope("storage.modifier")
        sto, sst = self.styles_for_scope("storage.type")
        lan, sla = self.styles_for_scope("constant.language")

        pun = self.view.style_for_scope("punctuation.section")
        key = self.view.style_for_scope("variable.parameter")
        equ = self.view.style_for_scope("keyword.operator.assignment")
        num = self.view.style_for_scope("constant.numeric")
        com = self.view.style_for_scope("punctuation.separator.comma")

        styles = {
            "con": con, "sco": sco, "flo": flo, "sfl": sfl, "mod": mod,
            "smo": smo, "sto": sto, "sst": sst, "lan": lan, "sla": sla,
            "pun": pun, "key": key, "equ": equ, "num": num, "com": com,
        }
        opts = {}
        for s, d in styles.items():
            opts["{}_style".format(s)] = "italic" if d.get("italic") else ""
            opts["{}_weight".format(s)] = "bold" if d.get("bold") else ""
            opts["{}_color".format(s)] = d.get("foreground")
            opts["{}_background".format(s)] = \
                d.get("background", "--background")

        return EXTRA_STYLE.format(**opts)

    def style_for_scope_punc(self, text):
        return self.view.style_for_scope(
            "{} punctuation.definition.backslash".format(text)
        )

    def styles_for_scope(self, text):
        return [
            self.view.style_for_scope(text), self.style_for_scope_punc(text)
        ]

    def on_navigate(self, href):
        type_, content = href[:4], href[5:]
        if type_ == "file":
            self.on_navigate_file(content)
        elif type_ == "copy":
            text = "<br><br>".join(
                s for s in self.html_cache[self.name][self.popup_name][:-1]
                if s
            )
            if content == "html":
                self.copy(html_css.pretty_print(text))
            elif content == "plain":
                self.copy(html_css.raw_print(text))

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
