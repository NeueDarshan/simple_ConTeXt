import sublime
import sublime_plugin
import threading
import string
import json
import os
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

EXTRA_STYLE = """
html {{
    --control-sequence-style: {con_style};
    --control-sequence-color: {con_color};
    --control-sequence-background: {con_background};

    --slash-control-sequence-style: {sco_style};
    --slash-control-sequence-color: {sco_color};
    --slash-control-sequence-background: {sco_background};

    --flow-control-sequence-style: {flo_style};
    --flow-control-sequence-color: {flo_color};
    --flow-control-sequence-background: {flo_background};

    --slash-flow-control-sequence-style: {sfl_style};
    --slash-flow-control-sequence-color: {sfl_color};
    --slash-flow-control-sequence-background: {sfl_background};

    --delimiter-style: {pun_style};
    --delimiter-color: {pun_color};
    --delimiter-background: {pun_background};

    --key-style: {key_style};
    --key-color: {key_color};
    --key-background: {key_background};

    --equals-style: {equ_style};
    --equals-color: {equ_color};
    --equals-background: {equ_background};

    --numeric-style: {num_style};
    --numeric-color: {num_color};
    --numeric-background: {num_background};

    --comma-style: {com_style};
    --comma-color: {com_color};
    --comma-background: {com_background};
}}
"""


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
            else:
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
                for k, v in sample:
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
        if not hasattr(self, "style"):
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
            return

        for location in locations:
            if scopes.enclosing_block(
                self.view, location - 1, self.size, scopes.FULL_CONTROL_SEQ
            ):
                return [
                    ["\\" + ctrl, ""]
                    for ctrl in self.cache[self.name].get_cmds()
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

        ctrl = scopes.enclosing_block(
            self.view, point, self.size, scopes.CONTROL_WORD
        )
        if not ctrl:
            return
        name = self.view.substr(sublime.Region(*ctrl))
        if name in self.cache.get(self.name, {}):
            self.view.show_popup(
                self.get_popup_text(name),
                location=ctrl[0],
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
                self.view, end, self.size, scopes.CONTROL_SEQ
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

        return TEMPLATE.format(
            body="<br><br>".join(
                s for s in self.html_cache[self.name][name] if s
            ),
            style=self.style,
            extra_style=self.get_extra_style(),
        )

    def get_extra_style(self):
        con = self.view.style_for_scope("support.function")
        sco = self.view.style_for_scope(
            "support.function punctuation.definition.backslash"
        )
        flo = self.view.style_for_scope("keyword.control")
        sfl = self.view.style_for_scope(
            "keyword.control punctuation.definition.backslash"
        )
        pun = self.view.style_for_scope("punctuation.section")
        key = self.view.style_for_scope("variable.parameter")
        equ = self.view.style_for_scope("keyword.operator.assignment")
        num = self.view.style_for_scope("constant.numeric")
        com = self.view.style_for_scope("punctuation.separator.comma")

        return EXTRA_STYLE.format(
            con_style="italic" if con.get("italic") else "",
            con_color=con.get("foreground"),
            con_background=con.get("background", "--background"),
            sco_style="italic" if sco.get("style") else "",
            sco_color=sco.get("foreground"),
            sco_background=sco.get("background", "--background"),
            flo_style="italic" if flo.get("style") else "",
            flo_color=flo.get("foreground"),
            flo_background=flo.get("background", "--background"),
            sfl_style="italic" if sfl.get("style") else "",
            sfl_color=sfl.get("foreground"),
            sfl_background=sfl.get("background", "--background"),
            pun_style="italic" if pun.get("style") else "",
            pun_color=pun.get("foreground"),
            pun_background=pun.get("background", "--background"),
            key_style="italic" if key.get("style") else "",
            key_color=key.get("foreground"),
            key_background=key.get("background", "--background"),
            equ_style="italic" if equ.get("style") else "",
            equ_color=equ.get("foreground"),
            equ_background=equ.get("background", "--background"),
            num_style="italic" if num.get("style") else "",
            num_color=num.get("foreground"),
            num_background=num.get("background", "--background"),
            com_style="italic" if com.get("style") else "",
            com_color=com.get("foreground"),
            com_background=com.get("background", "--background"),
        )

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
