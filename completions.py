import sublime
import sublime_plugin
import json
import re
import os

COMMAND_LEN_UPPER_BOUND = 100

def load_commands():
    commands_json = os.path.join(
        sublime.packages_path(), "ConTeXtTools", "commands.json")
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
    return protect_html_whitespace(protect_html_brackets(string))

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
            ["\\{name}".format(name=name), ""] for name in self.command_names]

    def on_query_completions(self, view, prefix, locations):
        if not is_context(view):
            return

        return self.command_completions

    def on_modified(self, view):
        if not is_context(view):
            return

        previous_text = view.substr(sublime.Region(
            max(0, view.sel()[0].begin() - COMMAND_LEN_UPPER_BOUND),
            view.sel()[0].begin()
        ))

        command_name = self.get_command_name(previous_text)
        if not command_name:
            view.hide_popup()
            return

        popup_text = self.get_popup_text(command_name)

        width = 8 * 75
        kwargs = {
            "location": -1,
            "max_width": width if width < 900 else 900,
            "flags": sublime.COOPERATE_WITH_AUTO_COMPLETE,
        }

        view.show_popup(popup_text, **kwargs)

    def get_command_name(self, previous_text):
        match = re.match(r"\s*([a-zA-Z]+)\\", previous_text[::-1])
        if match:
            name = match.group(1)[::-1]
            if name in self.command_names:
                return name

    def get_popup_text(self, command_name):
        style_sheet = "\n".join([
            r"html {",
            r"    background-color: #{};".format("151515"),
            r"}",
            r"",
            r".syntax {",
            r"    color: #{};".format("8ea6b7"),
            r"    font-size: 1.2em;",
            r"}",
            r"",
            r".doc_string {",
            r"    color: #{};".format("956837"),
            r"    font-size: 1em;",
            r"}",
        ])

        signatures = []
        command = self.commands[command_name]
        for variation in command:
            new_signature = "\n".join([
                r"<div class='syntax'>",
                r"    <code>{syntax}</code>",
                r"</div>",
                r"",
                r"<br />",
                r"",
                r"<div class='doc_string'>",
                r"    <code>{doc_string}</code>",
                r"</div>",
            ])
            parts = {
                "syntax": protect_html(variation[0]),
                "doc_string": protect_html(variation[1])
            }
            signatures.append(new_signature.format(**parts))

        full_signature = \
            r"<style>{style_sheet}</style>".format(style_sheet=style_sheet) \
            + "<br />".join(signatures)

        return full_signature
