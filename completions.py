import sublime
import sublime_plugin
import json
import re
import os

# longest seems to be \currentlistentrydestinationattribute at 36
COMMAND_LEN_UPPER_BOUND = 40


def load_commands():
    this_package_path = os.path.dirname(__file__)
    commands_json = os.path.join(this_package_path, "commands.json")
    with open(commands_json) as f:
        return json.load(f)


def protect_html_whitespace(string):
    return string.replace(" ", "&nbsp;").replace("\n", "<br />")


# we use <u> style markup to indicate default arguments in commands.json,
# so we give special attention to preserving those tags
def protect_html_brackets(string, ignore_tags=["u"]):
    new_string = string.replace("<", "&lt;").replace(">", "&gt;")
    for tag in ignore_tags:
        new_string = new_string.replace(
            "&lt;{tag}&gt;".format(tag=tag),
            "<{tag}>".format(tag=tag))
        new_string = new_string.replace(
            "&lt;/{tag}&gt;".format(tag=tag),
            "</{tag}>".format(tag=tag))
    return new_string


def protect_html(string, ignore_tags=["u"]):
    return protect_html_whitespace(
        protect_html_brackets(string, ignore_tags=ignore_tags))


def is_context(view):
    try:
        return view.match_selector(
            view.sel()[0].begin(), "text.tex.context")
    except:
        return False


class ContextMacroSignatureEventListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = load_commands()
        self.command_names = set(self.commands.keys())
        self.command_completions = [
            ["\\{name}".format(name=name), ""]
            for name in self.command_names]
        self.reload_settings()

    def reload_settings(self):
        self.settings = sublime.load_settings("ConTeXtTools.sublime-settings")

    def on_query_completions(self, view, prefix, locations):
        if not is_context(view):
            return

        return self.command_completions

    def on_modified(self, view):
        self.reload_settings()
        should_show_popup = is_context(view) \
            and self.settings.get("command_popups", {}).get("on")
        if not should_show_popup:
            return

        previous_text_range = [
            max(0, view.sel()[0].begin() - COMMAND_LEN_UPPER_BOUND),
            view.sel()[0].begin()
        ]

        command_name = self.get_command_name(view, *previous_text_range)
        if not command_name:
            view.hide_popup()
            return

        popup_text = self.get_popup_text(command_name)
        kwargs = {
            "location": -1,
            "max_width": 600,
            "flags": sublime.COOPERATE_WITH_AUTO_COMPLETE,
        }
        view.show_popup(popup_text, **kwargs)

    def get_command_name(self, view, start, stop):
        previous_text = view.substr(sublime.Region(start, stop))
        match = re.match(r"[^\S\n]*([a-zA-Z]+)\\", previous_text[::-1])
        if match:
            name = match.group(1)[::-1]
            range_ = [stop - end for end in reversed(match.span(1))]
            scope_is_command = view.match_selector(
                range_[0],
                ", ".join([
                    "support.function.control-word.context",
                    "keyword.control-word.context",
                    "entity.control-word.tex.context"
                ])
            )
            if name in self.command_names and scope_is_command:
                return name

    def get_popup_text(self, command_name):
        style_sheet = """
            html {{
                background-color: {background_color};
            }}
            .syntax {{
                color: {syntax_color};
                font-size: 1.2em;
            }}
            .doc_string {{
                color: {doc_string_color};
                font-size: 1em;
            }}
            .files {{
                color: {file_color};
                font-size: 1em;
            }}
        """.format(
            background_color="#151515",
            syntax_color="#8ea6b7",
            doc_string_color="#956837",
            file_color="#8ea6b7")

        signatures = []
        command = self.commands[command_name]
        files = command[-1]
        for variation in command[:-1]:
            new_signature = """
                <div class='syntax'>
                    <code>{syntax}</code>
                </div>
            """
            parts = {
                "syntax": protect_html(variation[0])
            }
            if len(variation[1]) > 0:
                new_signature += """
                    <br />
                    <div class='doc_string'>
                        <code>{doc_string}</code>
                    </div>
                """
                parts["doc_string"] = protect_html(variation[1])
            signatures.append(new_signature.format(**parts))

        full_signature = \
            "<style>{style_sheet}</style>".format(style_sheet=style_sheet) \
            + "<br />".join(signatures)

        if files and self.settings.get("command_popups", {}).get("show_file"):
            full_signature += """
                <br />
                <div class='files'>
                    <code>{files}</code>
                </div>
            """.format(files=protect_html(" ".join(files)))

        return full_signature
