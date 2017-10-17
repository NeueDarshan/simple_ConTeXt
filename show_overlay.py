import sublime
import sublime_plugin
import re
from .scripts import utilities
from .scripts import scopes


SCOPES = {
    "reference": [
        ("", scopes.REFERENCE),
    ],
    "heading": [
        # (" " * 0, scopes.HEADING),
        (" " * 0, scopes.DOCUMENT),
        # (" " * 0, scopes.OTHER),
        (" " * 0, scopes.PART),
        (" " * 2, scopes.CHAPTER),
        (" " * 4, scopes.SECTION),
        (" " * 6, scopes.SUBSECTION),
        (" " * 8, scopes.SUB2SECTION),
        (" " * 10, scopes.SUB3SECTION),
        (" " * 12, scopes.SUB4SECTION),
    ],
    "definition": [
        # ("", scopes.DEFINE_TEX),
        # ("", scopes.DEFINE_CONTEXT),
        ("", scopes.DEFINE),
    ],
    "file_name": [
        ("", scopes.FILE_NAME),
    ],
}


#D Strip braces and whitespace
def general_clean(text):
    match = re.match(r"^\s*{\s*(.*?)\s*}\s*", text)
    if match:
        return match.group(1)
    else:
        return text.strip()


#D Strip leading slash from command name
def def_clean(text):
    text = general_clean(text)
    if text.startswith("\\"):
        return text[1:]
    else:
        return text


class SimpleContextInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        offset = 0
        for region in self.view.sel():
            offset += self.view.insert(edit, region.begin() + offset, text)


class SimpleContextShowSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit, regions):
        if regions:
            middle_region = regions[len(regions) // 2]
            self.view.sel().clear()
            self.view.sel().add_all([sublime.Region(*tup) for tup in regions])
            self.view.show_at_center(sublime.Region(*middle_region))


class SimpleContextShowOverlayCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self.reload_view()

    def reload_view(self):
        self.view = self.window.active_view()

    def is_visible(self):
        return scopes.is_context(self.view)

    #D For our use, we give a descriptive name as a \type{scope}. But you can
    #D override this by providing a \type{scope_raw} instead.
    def run(
        self,
        scope="heading",
        scope_raw=None,
        on_choose=None,
        selected_index="closest"
    ):
        self.reload_settings()
        if not self.view:
            return
        self.orig_sel = [(region.a, region.b) for region in self.view.sel()]
        self.on_choose = on_choose

        if scope in SCOPES.keys():
            clean = def_clean if scope == "definition" else general_clean
            data = []
            for prefix, selector in SCOPES[scope]:
                for region in self.view.find_by_selector(selector):
                    data.append(
                        (
                            region.begin(),
                            region.end(),
                            prefix + clean(self.view.substr(region))
                        )
                    )
            data = sorted(data, key=lambda tup: tup[0])
            self.matches = [tup[:2] for tup in data]
            matches = [tup[2] for tup in data]
        elif scope_raw is not None:
            self.matches = sorted(
                [
                    (region.begin(), region.end())
                    for region in self.view.find_by_selector(scope_raw)
                ],
                key=lambda tup: tup[0],
            )
            matches = [
                general_clean(self.view.substr(sublime.Region(*tup)))
                for tup in self.matches
            ]
        else:
            return

        if selected_index in ["closest", "previous", "next"]:
            sel = self.view.sel()
            num_matches = len(self.matches)
            num_regions = len(sel)
            if num_regions > 0 and num_matches > 0:
                middle_region = sel[num_regions // 2]
                sequence = [
                    i for i in range(num_matches) if self.filter(
                        self.matches[i][0] - middle_region.begin(),
                        selected_index,
                    )
                ]
                if len(sequence) > 0:
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

    def filter(self, delta, mode):
        if mode == "closest":
            return True
        elif mode == "previous":
            return delta <= 0
        elif mode == "next":
            return delta >= 0

    def key_function(self, region):
        return lambda i: -abs(self.matches[i][0] - region.begin())

    def on_done(self, index):
        self.reload_view()
        if not self.view:
            return
        if 0 <= index < len(self.matches):
            tup = self.matches[index]
            if self.on_choose == "insert":
                text = self.view.substr(sublime.Region(*tup))
                self.view.run_command(
                    "simple_context_show_selection", {"regions": self.orig_sel}
                )
                self.view.run_command(
                    "simple_context_insert_text", {"text": text}
                )
            else:
                self.view.run_command(
                    "simple_context_show_selection", {"regions": [tup]}
                )
        else:
            self.view.run_command(
                "simple_context_show_selection", {"regions": self.orig_sel}
            )

    def on_highlight(self, index):
        if 0 <= index < len(self.matches):
            tup = self.matches[index]
            self.view.run_command(
                "simple_context_show_selection", {"regions": [tup]}
            )
