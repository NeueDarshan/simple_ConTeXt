# import sublime
import sublime_plugin

# from .tests import test_deep_dict


class SimpleContextRunTestsCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        self.window.run_command("simple_context_test_parse_bib_files")
        # self.window.run_command("simple_context_test_deep_dict")


# class SimpleContextTestDeepDictCommand(sublime_plugin.WindowCommand):
#     def run(self):
#         test_deep_dict.main()
