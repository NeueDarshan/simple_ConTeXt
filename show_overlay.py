import re

import sublime
import sublime_plugin

from .scripts import scopes


SELECTORS = {
    "buffer_name": (
        ("🗌 ", "", scopes.BUFFER),
    ),
    "definition": (
        # ("→" , "", scopes.DEFINE),
        ("→ ", "", scopes.DEFINE_TEX),
        ("→ ", "", scopes.DEFINE_CONTEXT),
    ),
    "file_name": (
        ("🔗 ", "", scopes.FILE_NAME),
    ),
    "heading": (
        # ("§ ", "  " * 0, scopes.HEADING),
        ("§ ", "  " * 0, scopes.DOCUMENT),
        # ("§ ", "  " * 0, scopes.OTHER),
        ("§ ", "  " * 0, scopes.PART),
        ("§ ", "  " * 1, scopes.CHAPTER),
        ("§ ", "  " * 2, scopes.SECTION),
        ("§ ", "  " * 3, scopes.SUBSECTION),
        ("§ ", "  " * 4, scopes.SUB2SECTION),
        ("§ ", "  " * 5, scopes.SUB3SECTION),
        ("§ ", "  " * 6, scopes.SUB4SECTION),
    ),
    "reference": (
        ("¶ ", "", scopes.REFERENCE),
    ),
}


def general_clean(text):
    """Strip braces and whitespace."""
    match = re.match(r"^\s*{\s*(.*?)\s*}\s*", text)
    if match:
        return match.group(1)
    return text.strip()


def default_clean(text):
    """Strip leading slash from command name."""
    text = general_clean(text)
    if text.startswith("\\"):
        return text[1:]
    return text


def filter_(delta, mode):
    if mode == "previous":
        return delta <= 0
    elif mode == "next":
        return delta >= 0
    # "closest"
    return True


class SimpleContextInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        offset = 0
        for region in self.view.sel():
            offset += self.view.insert(
                edit, region.begin() + offset, general_clean(text),
            )


class SimpleContextShowSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit, regions):
        if regions:
            mid = regions[len(regions) // 2]
            self.view.sel().clear()
            self.view.sel().add_all([sublime.Region(*tup) for tup in regions])
            self.view.show_at_center(sublime.Region(*mid))


class SimpleContextHighlightSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit, regions):
        if regions:
            mid = regions[len(regions) // 2]
            self.view.show_at_center(sublime.Region(*mid))
            self.view.add_regions(
                "simple_ConTeXt_show_selection",
                [sublime.Region(*tup) for tup in regions],
                scope="comment",
                flags=sublime.DRAW_NO_FILL,
            )


class SimpleContextUnHighlightSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase_regions("simple_ConTeXt_show_selection")


class SimpleContextShowOverlayCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        return (
            scopes.is_context(self.window.active_view())
            if self.window else False
        )

    # For our use, we give a descriptive name as a \type{selector}. But you can
    # override this by providing a \type{selector_raw} instead.
    def run(
        self,
        prefix=False,
        selector="heading",
        selector_raw=None,
        on_choose=None,
        selected_index="closest",
    ):
        self.view = self.window.active_view()
        if not self.view:
            return
        self.orig_sel = tuple((reg.a, reg.b) for reg in self.view.sel())
        self.on_choose = on_choose

        if selector_raw is not None:
            self.matches = sorted(
                [
                    (region.begin(), region.end())
                    for region in self.view.find_by_selector(selector_raw)
                ],
                key=lambda tup: tup[0],
            )
            matches = [
                general_clean(self.view.substr(sublime.Region(*tup)))
                for tup in self.matches
            ]
        elif selector in SELECTORS.keys():
            clean = \
                default_clean if selector == "definition" else general_clean
            data = []
            for pre, space, sel in SELECTORS[selector]:
                for region in self.view.find_by_selector(sel):
                    text = pre if prefix else ""
                    text += space + clean(self.view.substr(region))
                    data.append((region.begin(), region.end(), text))
            data = sorted(data, key=lambda tup: tup[0])
            matches = [tup[2] for tup in data]
            self.matches = [tup[:2] for tup in data]
        else:
            return

        self.run_aux(selected_index, matches)

    def run_aux(self, sel_index, all_matches):
        if sel_index in {"closest", "previous", "next"}:
            sel = self.view.sel()
            matches = len(self.matches)
            regions = len(sel)
            if regions and matches:
                mid = sel[regions // 2]
                seq = {
                    i for i in range(matches)
                    if filter_(self.matches[i][0] - mid.begin(), sel_index)
                }
                index = max(seq, key=self.key_function(mid)) if seq else 0
            else:
                index = 0
        elif isinstance(sel_index, int) and not isinstance(sel_index, bool):
            index = sel_index
        else:
            index = 0

        self.window.show_quick_panel(
            all_matches,
            self.on_done,
            on_highlight=self.on_highlight,
            selected_index=index,
        )

    def key_function(self, region):
        return lambda i: -abs(self.matches[i][0] - region.begin())

    def on_done(self, index):
        self.view = self.window.active_view()
        if not self.view:
            return

        # self.view.run_command("simple_context_un_highlight_selection")
        if 0 <= index < len(self.matches):
            tup = self.matches[index]
            if self.on_choose == "insert":
                text = self.view.substr(sublime.Region(*tup))
                self.view.run_command(
                    "simple_context_show_selection",
                    {"regions": self.orig_sel},
                )
                self.view.run_command(
                    "simple_context_insert_text", {"text": text},
                )
            else:
                self.view.run_command(
                    "simple_context_show_selection", {"regions": (tup,)},
                )
        else:
            self.view.run_command(
                "simple_context_show_selection", {"regions": self.orig_sel},
            )

    def on_highlight(self, index):
        if 0 <= index < len(self.matches):
            tup = self.matches[index]
            # self.view.run_command(
            #     "simple_context_highlight_selection", {"regions": (tup,)},
            # )
            self.view.run_command(
                "simple_context_show_selection", {"regions": (tup,)},
            )


class SimpleContextShowCombinedOverlayCommand(sublime_plugin.WindowCommand):
    prev_sels = None

    def is_visible(self):
        return (
            scopes.is_context(self.window.active_view())
            if self.window else False
        )

    def update_view(self):
        window = self.window
        if window:
            view = window.active_view()
            if view:
                self.view = view
            else:
                self.view = None
        else:
            self.view = None

    def run(
        self,
        selectors=None,
        default_selectors=None,
        remember_previous_selectors=True,
        on_choose=None,
        prefix=True,
        selected_index="closest",
    ):
        self.update_view()
        if not self.view:
            return
        self.orig_sel = tuple((reg.a, reg.b) for reg in self.view.sel())
        self.on_choose = on_choose
        self.prefix = prefix

        self.init_selectors(selectors, default_selectors)
        if remember_previous_selectors and self.prev_sels is not None:
            self.cur_sels = self.prev_sels.copy()
        else:
            self.cur_sels = {k: True for k in self.def_sels}

        self.compute_data()
        self.run_panel(selected_index=selected_index)

    def init_selectors(self, selectors, default_selectors):
        if selectors is None:
            self.selectors = sorted(SELECTORS.keys())
        elif isinstance(selectors, list):
            self.selectors = sorted(selectors)
        elif isinstance(selectors, str):
            self.selectors = [selectors]

        if default_selectors is None:
            self.def_sels = self.selectors.copy()
        elif isinstance(default_selectors, list):
            self.def_sels = sorted(default_selectors)
        elif isinstance(default_selectors, str):
            self.def_sels = [default_selectors]

    def run_panel(self, selected_index=None):
        index = 0 if selected_index is None else self.get_index(selected_index)
        self.window.show_quick_panel(
            ["Change scopes shown"] + self.get_current_entries(),
            self.run_handle,
            on_highlight=self.on_highlight,
            selected_index=index,
        )

    def compute_data(self):
        self.update_view()
        if not self.view:
            return
        self.data = {}
        for sel in self.selectors:
            tup = SELECTORS.get(sel)
            clean = default_clean if sel == "definition" else general_clean
            for pre, space, scope in tup:
                for reg in self.view.find_by_selector(scope):
                    text = (
                        (pre if self.prefix else "") + space +
                        clean(self.view.substr(reg))
                    )
                    self.data[(reg.begin(), reg.end())] = (sel, text)
        self.sorted_data = sorted(self.data.items(), key=lambda tup: tup[0])
        self.get_current_entries(result=False)

    def get_current_entries(self, result=True):
        self.current_entries = [
            (pos, data[1]) for pos, data in self.sorted_data
            if self.cur_sels.get(data[0])
        ]
        if result:
            return [tup[1] for tup in self.current_entries]
        return None

    def get_index(self, sel_index):
        if sel_index in {"closest", "previous", "next"}:
            self.update_view()
            if self.view:
                sel = self.view.sel()
                matches = len(self.current_entries)
                regions = len(sel)
                if regions and matches:
                    mid = sel[regions // 2]
                    seq = {
                        i for i in range(matches) if filter_(
                            self.current_entries[i][0][0] - mid.begin(),
                            sel_index,
                        )
                    }
                    if seq:
                        return 1 + max(seq, key=self.key_function(mid))
        elif isinstance(sel_index, int) and not isinstance(sel_index, bool):
            return 1 + sel_index
        return 1

    def key_function(self, region):
        return lambda i: -abs(self.current_entries[i][0][0] - region.begin())

    def on_highlight(self, index):
        if 0 <= index - 1 < len(self.current_entries):
            sel = self.current_entries[index - 1][0]
            # self.view.run_command(
            #     "simple_context_highlight_selection", {"regions": (sel,)},
            # )
            self.view.run_command(
                "simple_context_show_selection", {"regions": (sel,)},
            )

    def run_handle(self, index):
        self.update_view()
        if not self.view:
            return
        if not index:
            self.run_panel_choose()
            return

        # self.view.run_command("simple_context_un_highlight_selection")
        if 0 <= index - 1 < len(self.current_entries):
            sel, text = self.current_entries[index - 1]
            if self.on_choose == "insert":
                self.view.run_command(
                    "simple_context_show_selection",
                    {"regions": self.orig_sel},
                )
                self.view.run_command(
                    "simple_context_insert_text", {"text": text},
                )
            else:
                self.view.run_command(
                    "simple_context_show_selection", {"regions": (sel,)},
                )
        else:
            self.view.run_command(
                "simple_context_show_selection", {"regions": self.orig_sel},
            )

    def run_panel_choose(self, selected_index=None):
        self.window.show_quick_panel(
            [["..", "go back"]] + self.get_selectors(),
            self.run_handle_choose,
            selected_index=0 if selected_index is None else selected_index,
        )

    def run_handle_choose(self, index):
        if index:
            if 0 <= index - 1 < len(self.selectors):
                key = self.selectors[index - 1]
                self.cur_sels[key] = not self.cur_sels.get(key)
                self.prev_sels = self.cur_sels.copy()
                self.run_panel_choose(selected_index=index)
        else:
            self.run_panel(selected_index="closest")

    def get_selectors(self):
        return [
            [k, "Yes" if self.cur_sels.get(k) else "No"]
            for k in self.selectors
        ]
