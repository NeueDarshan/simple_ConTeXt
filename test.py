import os
import subprocess
import threading
import time

import sublime
import sublime_api
import sublime_plugin


def prefix_lines(pre: str, text: str) -> str:
    return "\n".join(pre + line for line in text.split("\n"))


class SimpleContextRunTestsCommand(sublime_plugin.WindowCommand):
    """
    This ST command is intended as a front-end to whatever tests we have set
    up. To invoke it, simply type

    ```python
    window.run_command("simple_context_run_tests")
    ```

    into the ST console.
    """

    def run(self) -> None:
        self.window.run_command("simple_context_test_parse_bib_files")
        self.window.run_command("simple_context_test_syntax_files")
        # Watch out: `simple_context_test_deep_dict` runs in a separate thread
        # as it takes longer.
        self.window.run_command("simple_context_test_deep_dict")


class SimpleContextTestDeepDictCommand(sublime_plugin.WindowCommand):
    """
    We cannot seem to add `hypothesis` as a dependency to `dependencies.json`,
    as it's not recognised.  So we resort to calling out to the system Python
    instead, assuming that such a thing exists and it can find `hypothesis` and
    is generally set up as needed.
    """

    def run(self) -> None:
        root = os.path.join(
            sublime.expand_variables(
                "${packages}", self.window.extract_variables(),
            ),
            "simple_ConTeXt",
            "tests",
        )
        proc = subprocess.Popen(
            ["python3", os.path.join(root, "test_deep_dict.py")],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        thread = threading.Thread(target=lambda: self.run_aux(proc))
        thread.start()

    def run_aux(self, proc: subprocess.Popen) -> None:
        out, err = proc.communicate()
        # I don't understand why we seem to be getting feedback through
        # `stderr` rather than `stdout`, but whatever.
        if err:
            err_ = err.decode(encoding="utf-8").strip()

            # Mess around with getting some nice formatting to our liking.
            if err_.endswith("OK"):
                err_text = "\n".join(l for l in err_.split("\n")[1:] if l)
            else:
                err_text = "\n".join(l for l in err_.strip("\n").split("\n"))

            print("[simple_ConTeXt] - test deep dict:")
            print(prefix_lines("[simple_ConTeXt]   - ", err_text))


class SimpleContextTestSyntaxFilesCommand(sublime_plugin.WindowCommand):
    """
    We rely on `sublime_api.run_syntax_test` to automatically perform the
    desired tests.
    """

    def run(self) -> None:
        print("[simple_ConTeXt] - test syntax files:")
        start_time = time.time()

        root = os.path.join("Packages", "simple_ConTeXt", "tests")
        tests = {
            "context": [os.path.join(root, "syntax_test_context.mkiv"), 0],
            "metapost": [os.path.join(root, "syntax_test_metapost.mp"), 0],
        }

        for name, tup in tests.items():
            path, _ = tup
            _, output_lines = sublime_api.run_syntax_test(path)
            fails = len(output_lines)
            tests[name][1] += fails

        total_errs = sum(v[1] for v in tests.values())
        if total_errs:
            for name, tup in tests.items():
                _, errors = tup
                if errors:
                    msg = \
                        "[simple_ConTeXt]   - failed to pass '{}' syntax test"
                    print(msg.format(name))
        else:
            msg = "[simple_ConTeXt]   - Ran {} tests in {:.3f}s"
            print(msg.format(len(tests), time.time() - start_time))
            print("[simple_ConTeXt]   - OK")
