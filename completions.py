import collections
import json
import os
import string
import threading
import time

from typing import Dict, Iterable, List, Optional, Union  # noqa

import sublime
import sublime_plugin

from .scripts import files
from .scripts import html_css
from .scripts import load
from .scripts import randomize
from .scripts import scopes
from .scripts import utilities


IDLE = 0

RUNNING = 1

TEMPLATE = """
<html>
    <style>
        {extra_style}
        {style}
    </style>
    <body id="simple-ConTeXt-pop-up">
        <div class="popup">
            {body}
        </div>
    </body>
</html>
"""


def extra_style() -> str:
    result = []
    suffixes = ("style", "weight", "color", "background")
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
        "wor": "keyword",
        "com": "comma",
        "par": "parameter",
    }

    for tag, pre in data.items():
        for suf in suffixes:
            for opt in ("", "slash"):
                result.append(
                    "--%s%scontrol-sequence-%s: {%s_%s};" % (
                        opt + "-" if opt else "",
                        pre + "-" if pre else "",
                        suf,
                        "s{:.2}".format(tag) if opt else tag,
                        suf,
                    )
                )

    for tag, pre in aux.items():
        for suf in suffixes:
            result.append("--%s-%s: {%s_%s};" % (pre, suf, tag, suf))

    return "html {{%s}}" % "\n".join(result)


EXTRA_STYLE = extra_style()


def try_jump_to_def(view: sublime.View, command: str) -> None:
    threading.Thread(target=lambda: try_jump_to_def_aux(view, command)).start()


def try_jump_to_def_aux(view: sublime.View, name: str) -> None:
    start_time = time.time()
    while view.is_loading():
        time.sleep(0.01)
        if time.time() - start_time > 1:
            return
    symbols = {strip_prefix(text): pos for (pos, text) in view.symbols()}
    if name in symbols:
        region = symbols[name]
        view.run_command(
            "simple_context_show_selection",
            {"regions": [(region.a, region.b)]},
        )


class VirtualCommandDict:
    def __init__(
        self,
        dir_: str,
        max_size: int = 100,
        local_size: int = 10,
        cmds: str = "_commands.json",
    ) -> None:
        self.dir = dir_
        self.missing = sorted(f for f in os.listdir(dir_) if f != cmds)
        with open(os.path.join(dir_, cmds), encoding="utf-8") as f:
            self.cmds = collections.OrderedDict()
            for text in sorted(json.load(f), key=lambda s: s.split(":", 1)[1]):
                parity, ctrl = text.split(":", 1)
                self.cmds[ctrl] = int(parity)
        self.local_size = local_size
        self.cache = utilities.FuzzyOrderedDict(max_size=max_size)

    def __setitem__(self, key, value) -> None:
        self.cache.add_left(key, value)

    def __getitem__(self, key) -> None:
        if key in self:
            if key in self.cache:
                return self.cache[key]
            name = min(f for f in self.missing if key <= f)
            with open(os.path.join(self.dir, name), encoding="utf-8") as f:
                data = json.load(f)

            sample = [
                (k, data[k])
                for k in randomize.safe_random_sample(
                    list(data), self.local_size,
                )
            ]
            self.cache.fuzzy_add_right(sample)

            result = data[key]
            self[key] = result
            return result
        else:
            raise KeyError

    def __len__(self) -> int:
        return len(self.cache)

    def __contains__(self, key) -> bool:
        return key in self.cmds


def strip_prefix(text: str) -> str:
    return "".join(text.split()[-1:])


class SimpleContextMacroSignatureEventListener(
    utilities.BaseSettings, sublime_plugin.ViewEventListener,
):
    cache = {}
    html_cache = {}
    lock = threading.Lock()
    loader = load.InterfaceLoader()
    state = IDLE
    file_min = 20000
    param_char = string.ascii_letters  # + string.whitespace
    extensions = (".mkix", ".mkxi", ".mkiv", ".mkvi", ".tex", ".mkii")
    auto_complete_cmd_key = None
    attempts = 0

    def is_visible(self) -> bool:
        return self.is_visible_alt()

    def reload_settings(self) -> None:
        super().reload_settings()
        self.pop_ups = {
            k.split("/")[-1]: self.get_setting("pop_ups/{}".format(k))
            for k in {
                "line_break",
                "match_indentation",
                "hang_indentation",
                "methods/on_hover",
                "methods/on_modified",
                "show_copy_pop_up",
                "show_source_files",
            }
        }
        self.name = files.file_as_slug(self.context_path)
        self.size = self.view.size()
        if (
            self.state == IDLE and
            self.is_visible() and
            self.name not in self.cache
        ):
            if self.get_setting("pop_ups/try_generate_on_demand"):
                self.state = RUNNING
                threading.Thread(target=self.reload_settings_aux).start()
            else:
                self.try_load_commands()

    def reload_settings_aux(self) -> None:
        self.view.window().run_command(
            "simple_context_regenerate_interface_files",
            {
                "do_all": False,
                "paths": [self.context_path],
                "overwrite": False,
            },
        )
        self.try_load_commands()
        self.state = IDLE

    def try_load_commands(self) -> None:
        self.attempts += 1
        if self.attempts < 10:
            self.load_commands(
                os.path.join(
                    sublime.packages_path(),
                    "simple_ConTeXt",
                    "interface",
                    self.name,
                )
            )

    def load_css(self) -> None:
        self.style = html_css.strip_css_comments(
            sublime.load_resource(
                "Packages/simple_ConTeXt/css/pop_up.css"
            )
        )

    def load_commands(self, path: str) -> None:
        try:
            self.cache[self.name] = \
                VirtualCommandDict(path, max_size=500, local_size=25)
            self.html_cache[self.name] = \
                utilities.LeastRecentlyUsedCache(max_size=500)
        except OSError:
            pass

    def on_query_completions(
        self, prefix: str, locations: List[int],
    ) -> Optional[List[List[str]]]:
        self.reload_settings()
        if self.state != IDLE or not self.is_visible():
            return None

        cmd = self.auto_complete_cmd_key
        if cmd is not None:
            self.auto_complete_cmd_key = None
            return self.complete_key(cmd)

        if self.name in self.cache:
            return self.complete_command(self.cache[self.name], locations)

        return None

    def complete_command(
        self, cache: VirtualCommandDict, locations: List[int],
    ) -> Optional[List[List[str]]]:
        for location in locations:
            if scopes.enclosing_block(
                self.view,
                location - 1,
                scopes.FULL_CONTROL_SEQ,
                end=self.size,
            ):
                result = []
                for ctrl, parity in cache.cmds.items():
                    if parity > 0:
                        entry = ["\\{}\t({}) command".format(ctrl, parity)]
                    else:
                        entry = ["\\{}\tcommand".format(ctrl)]
                    entry.append("\\{}$0".format(ctrl))
                    result.append(entry)
                return result
        return None

    # Crude, does a decent job though.
    def complete_key(self, cmd: str, limit: int = 2):
        return self.complete_key_aux(cmd, intermediate=False, limit=limit)

    # For now, just handle the possibility of multiple variations by
    # merging them all. Watch out for infinite recursion.
    def complete_key_aux(
        self, cmd: str, intermediate: bool = False, limit: int = 3,
    ):
        result = {}  # type: Dict[str, List[str]]
        for var in cmd:
            if not isinstance(var, dict):
                continue
            content = var.get("con")
            if isinstance(content, dict):
                content = [content]
            if not isinstance(content, list) or not content:
                continue
            for arg in content:
                if not isinstance(arg, dict):
                    continue
                con = arg.get("con")
                if isinstance(con, dict):
                    for k in con:
                        if k.isalpha():
                            result[k] = [
                                "{}\t{}".format(k, "option"),
                                "{}=$1, $0".format(k),
                            ]
                inh_orig = arg.get("inh")
                if inh_orig is None:
                    continue
                inhs = [inh_orig] if isinstance(inh_orig, str) else inh_orig
                for inh in inhs:
                    if (
                        limit > 0 and
                        self.name in self.cache and
                        inh in self.cache.get(self.name, {})
                    ):
                        inh_cmd = self.cache[self.name][inh]
                        result.update(
                            self.complete_key_aux(
                                inh_cmd, intermediate=True, limit=limit - 1,
                            )
                        )

        if intermediate:
            return result
        return sorted(result.values()) if result else None

    def on_hover(self, point: int, hover_zone: int) -> None:
        if not self.is_visible() or hover_zone != sublime.HOVER_TEXT:
            return

        self.reload_settings()
        if (
            self.state != IDLE or
            not self.get_setting("pop_ups/methods/on_hover") or
            not self.is_visible()
        ):
            self.view.hide_popup()
            return

        ctrl = scopes.enclosing_block(
            self.view, point, scopes.CONTROL_WORD, end=self.size,
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
                on_navigate=lambda href: self.on_navigate(href, name),
            )
        else:
            self.view.hide_popup()

    def on_modified_async(self) -> None:
        self.reload_settings()
        if self.state != IDLE or not self.is_visible():
            self.view.hide_popup()
            return

        selection = self.view.sel()
        if not selection:
            return
        sel = selection[0]
        end = sel.end()
        end_ = end - 1 if end < self.size else end

        if self.get_setting("pop_ups/methods/on_modified"):
            ctrl = scopes.left_enclosing_block(
                self.view, end_, scopes.CONTROL_SEQ, end=self.size
            )
            if ctrl:
                name = self.view.substr(sublime.Region(*ctrl))
                if name in self.cache.get(self.name, {}):
                    self.view.show_popup(
                        self.get_popup_text(name),
                        location=ctrl[0] - 1,
                        max_width=600,
                        flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                        on_navigate=lambda href: self.on_navigate(href, name),
                    )
                    return

        if self.get_setting("option_completions/on"):
            ctrl = scopes.last_block_in_region(
                self.view,
                0,
                scopes.CONTROL_SEQ,
                end=end_,
                skip=scopes.SKIP_ARGS_AND_SPACES,
            )
            if (
                ctrl and
                self.view.substr(end - 1) in string.ascii_letters and
                self.view.match_selector(end - 1, scopes.BRACKETS_NOT_VALUE)
            ):
                name = self.view.substr(sublime.Region(*ctrl))
                if name in self.cache.get(self.name, {}):
                    self.auto_complete_cmd_key = self.cache[self.name][name]
                    self.view.run_command(
                        "auto_complete",
                        {
                            "disable_auto_insert": True,
                            "api_completions_only": True,
                        },
                    )
                    return

        self.view.hide_popup()

    def get_popup_text(self, name: str) -> str:
        new_pop_up_state = json.dumps(self.pop_ups, sort_keys=True)
        if not hasattr(self, "prev_pop_up_state"):
            self.prev_pop_up_state = None
        if new_pop_up_state != self.prev_pop_up_state:
            self.html_cache[self.name].clear()
        if name not in self.html_cache[self.name]:
            cmd = self.cache[self.name][name]
            self.html_cache[self.name][name] = self.loader.load(
                name, cmd, protect_space=True, **self.pop_ups
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

    def get_extra_style(self) -> str:
        con, sco = self.styles_for_scope("support.function")
        flo, sfl = self.styles_for_scope("keyword.control")
        mod, smo = self.styles_for_scope("storage.modifier")
        sto, sst = self.styles_for_scope("storage.type")
        lan, sla = self.styles_for_scope("constant.language")

        pun = self.view.style_for_scope("punctuation.section")
        key = self.view.style_for_scope("variable.parameter")
        equ = self.view.style_for_scope("keyword.operator.assignment")
        num = self.view.style_for_scope("constant.numeric")
        wor = self.view.style_for_scope("keyword.other")
        com = self.view.style_for_scope("punctuation.separator.comma")
        par = self.view.style_for_scope("variable.parameter")

        styles = {
            "con": con, "sco": sco, "flo": flo, "sfl": sfl, "mod": mod,
            "smo": smo, "sto": sto, "sst": sst, "lan": lan, "sla": sla,
            "pun": pun, "key": key, "equ": equ, "num": num, "com": com,
            "par": par, "wor": wor,
        }
        opts = {}
        for s, d in styles.items():
            opts["{}_style".format(s)] = "italic" if d.get("italic") else ""
            opts["{}_weight".format(s)] = "bold" if d.get("bold") else ""
            opts["{}_color".format(s)] = d.get("foreground")
            opts["{}_background".format(s)] = \
                d.get("background", "--background")

        return EXTRA_STYLE.format(**opts)

    def style_for_scope_punc(self, text: str) -> str:
        return self.view.style_for_scope(
            "{} punctuation.definition.backslash".format(text)
        )

    def styles_for_scope(self, text: str) -> List[str]:
        return [
            self.view.style_for_scope(text), self.style_for_scope_punc(text),
        ]

    def on_navigate(self, href: str, name: str) -> None:
        type_, content = href[:4], href[5:]
        if type_ == "file":
            self.on_navigate_file(content, name)
        elif type_ == "copy":
            text = "<br><br>".join(
                s for s in self.html_cache[self.name][self.popup_name][:-1]
                if s
            )
            self.copy(html_css.raw_print(text))
            # if content == "html":
            #     self.copy(html_css.pretty_print(text))
            # elif content == "plain":
            #     self.copy(html_css.raw_print(text))

    def on_navigate_file(self, name: str, command: str) -> None:
        threading.Thread(
            target=lambda: self.on_navigate_file_aux(name, command)
        ).start()

    def on_navigate_file_aux(self, name: str, command: str) -> None:
        main = files.locate(
            self.context_path, name, flags=self.flags, shell=self.shell,
        )
        if main and os.path.exists(main):
            view = self.view.window().open_file(main)
            try_jump_to_def(view, command)
            return

        other = files.fuzzy_locate(
            self.context_path,
            name,
            extensions=self.extensions,
            flags=self.flags,
            shell=self.shell,
        )
        if other and os.path.exists(other):
            view = self.view.window().open_file(other)
            try_jump_to_def(view, command)
            return

        sublime.message_dialog('Falied to locate file "{}".'.format(name))

    def copy(self, text: str) -> None:
        self.view.hide_popup()
        sublime.set_clipboard(text)
        sublime.status_message("Pop-up content copied to clipboard")
