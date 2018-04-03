import collections
import re

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import scopes


SELECTORS = {
    "reference": [
        ("¶ ", "", scopes.REFERENCE),
    ],
    "heading": [
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
    ],
    "definition": [
        # ("→" , "", scopes.DEFINE),
        ("→ ", "", scopes.DEFINE_TEX),
        ("→ ", "", scopes.DEFINE_CONTEXT),
    ],
    "file_name": [
        ("🔗 ", "", scopes.FILE_NAME),
    ],
}


# Strip braces and whitespace.
def general_clean(text):
    match = re.match(r"^\s*{\s*(.*?)\s*}\s*", text)
    if match:
        return match.group(1)
    return text.strip()


# Strip leading slash from command name.
def def_clean(text):
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
            middle_region = regions[len(regions) // 2]
            self.view.sel().clear()
            self.view.sel().add_all([sublime.Region(*tup) for tup in regions])
            self.view.show_at_center(sublime.Region(*middle_region))


class SimpleContextHighlightSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit, regions):
        if regions:
            middle_region = regions[len(regions) // 2]
            self.view.show_at_center(sublime.Region(*middle_region))
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
    def reload_settings(self):
        utilities.reload_settings(self)
        self.reload_view()

    def reload_view(self):
        self.view = self.window.active_view()

    def is_visible(self):
        return scopes.is_context(self.view)

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
        self.reload_settings()
        if not self.view:
            return
        self.orig_sel = [(region.a, region.b) for region in self.view.sel()]
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
            clean = def_clean if selector == "definition" else general_clean
            data = []
            for prefix_str, space, sel in SELECTORS[selector]:
                for region in self.view.find_by_selector(sel):
                    data.append(
                        (
                            region.begin(),
                            region.end(),
                            (prefix_str if prefix else "") + space +
                            clean(self.view.substr(region)),
                        )
                    )
            data = sorted(data, key=lambda tup: tup[0])
            self.matches = [tup[:2] for tup in data]
            matches = [tup[2] for tup in data]
        else:
            return

        if selected_index in ["closest", "previous", "next"]:
            sel = self.view.sel()
            num_matches = len(self.matches)
            num_regions = len(sel)
            if num_regions > 0 and num_matches > 0:
                middle_region = sel[num_regions // 2]
                sequence = [
                    i for i in range(num_matches) if filter_(
                        self.matches[i][0] - middle_region.begin(),
                        selected_index,
                    )
                ]
                if sequence:
                    index = max(sequence, key=self.key_function(middle_region))
                else:
                    index = 0
            else:
                index = 0
        else:
            index = selected_index

        self.window.show_quick_panel(
            matches,
            self.on_done,
            on_highlight=self.on_highlight,
            selected_index=index,
        )

    def key_function(self, region):
        return lambda i: -abs(self.matches[i][0] - region.begin())

    def on_done(self, index):
        self.reload_view()
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
                    "simple_context_show_selection", {"regions": [tup]},
                )
        else:
            self.view.run_command(
                "simple_context_show_selection", {"regions": self.orig_sel},
            )

    def on_highlight(self, index):
        if 0 <= index < len(self.matches):
            tup = self.matches[index]
            # self.view.run_command(
            #     "simple_context_highlight_selection", {"regions": [tup]},
            # )
            self.view.run_command(
                "simple_context_show_selection", {"regions": [tup]},
            )


class SimpleContextShowCombinedOverlayCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self.reload_view()

    def reload_view(self):
        self.view = self.window.active_view()

    def is_visible(self):
        return scopes.is_context(self.view)

    def run(
        self,
        selectors=SELECTORS.keys(),
        active_selectors=SELECTORS.keys(),
        selectors_raw=[],
        active_selectors_raw=[],
        on_choose=None,
        prefix=True,
        selected_index="closest",
    ):
        self.reload_settings()
        if not self.view:
            return
        self.orig_sel = [(region.a, region.b) for region in self.view.sel()]
        self.on_choose = on_choose
        self.prefix = prefix

        self.selectors = collections.OrderedDict()
        self.active_selectors = set()
        temp = {}
        for selector in selectors_raw:
            temp[selector] = [("", "", selector)]
            if selector in active_selectors_raw:
                self.active_selectors.add(selector)
        for selector in selectors:
            if selector in SELECTORS:
                temp[selector] = SELECTORS[selector]
                if selector in active_selectors:
                    self.active_selectors.add(selector)
        for k, v in sorted(temp.items(), key=lambda tup: tup[0]):
            self.selectors[k] = v

        self.selected_index = selected_index
        self.run_panel()

    def run_panel(self, selected_index=None):
        self.update_data()
        self.check_history()
        self.window.show_quick_panel(
            self.get_data() + ["Choose scopes:"],
            self.run_handle,
            on_highlight=self.on_highlight,
            selected_index=(
                selected_index if selected_index is not None
                else self.last_choice
            ),
        )

    def get_data(self):
        return [tup[2] for tup in self.data]

    def update_data(self):
        selectors = []
        for k, v in self.selectors.items():
            if k in self.active_selectors:
                selectors += [(k,) + tup for tup in v]
        data = []
        for type_, prefix, space, selector in selectors:
            clean = def_clean if type_ == "definition" else general_clean
            for region in self.view.find_by_selector(selector):
                data.append(
                    (
                        region.begin(),
                        region.end(),
                        (prefix if self.prefix else "") + space +
                        clean(self.view.substr(region)),
                    )
                )
        self.data = sorted(data, key=lambda tup: tup[0])

    def check_history(self):
        self.last_choice = 0
        if self.selected_index in ["closest", "previous", "next"]:
            sel = self.view.sel()
            num_matches = len(self.data)
            num_regions = len(sel)
            if num_regions > 0 and num_matches > 0:
                middle_region = sel[num_regions // 2]
                sequence = [
                    i for i in range(num_matches) if filter_(
                        self.data[i][0] - middle_region.begin(),
                        self.selected_index,
                    )
                ]
                if sequence:
                    self.last_choice += \
                        max(sequence, key=self.key_function(middle_region))
        else:
            self.last_choice += self.selected_index

    def key_function(self, region):
        return lambda i: -abs(self.data[i][0] - region.begin())

    def on_highlight(self, index):
        if 0 <= index < len(self.data):
            tup = self.data[index][:2]
            # self.view.run_command(
            #     "simple_context_highlight_selection", {"regions": [tup]},
            # )
            self.view.run_command(
                "simple_context_show_selection", {"regions": [tup]},
            )

    def run_handle(self, index):
        self.reload_view()
        if not self.view:
            return
        # self.view.run_command("simple_context_un_highlight_selection")
        if index >= len(self.data):
            self.run_panel_choose(selected_index=0)
        elif index >= 0:
            tup = self.data[index][:2]
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
                    "simple_context_show_selection", {"regions": [tup]},
                )
        else:
            self.view.run_command(
                "simple_context_show_selection", {"regions": self.orig_sel},
            )

    def run_panel_choose(self, selected_index=None):
        self.window.show_quick_panel(
            [["..", "go back"]] + self.get_selectors(),
            self.run_handle_choose,
            on_highlight=self.on_highlight_choose,
            selected_index=(
                selected_index if selected_index is not None
                else self.last_choice
            ),
        )

    def on_highlight_choose(self, index):
        pass

    def run_handle_choose(self, index):
        if index == 0:
            self.run_panel()
        else:
            self.last_choice = index
            index -= 1
            if 0 <= index < len(self.selectors):
                key = self.get_selector(index)
                if key in self.active_selectors:
                    self.active_selectors.remove(key)
                else:
                    self.active_selectors.add(key)
                self.run_panel_choose()
            else:
                return

    def get_selectors(self):
        return [
            [k, "Yes" if k in self.active_selectors else "No"]
            for k in self.selectors
        ]

    def get_selector(self, index):
        keys = list(self.selectors.keys())
        return keys[index]
