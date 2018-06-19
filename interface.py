import threading
import time
import json
import os

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import files
from .scripts import save


IDLE = 0

RUNNING = 1


def arg_count(cmd):
    """Return the maximum number of arguments the given command takes."""
    count = 0
    for var in cmd:
        if not var:
            n = 0
        elif isinstance(var, dict):
            n = arg_count_aux([var])
        elif isinstance(var, list):
            n = arg_count_aux(var)
        else:
            n = 0
        count = max(count, n)
    return count


def arg_count_aux(list_):
    count = 0
    for var in list_:
        n = 0
        if isinstance(var, dict):
            con = var.get("con")
            if isinstance(con, list):
                n += arg_count_aux_i(con)
            elif isinstance(con, dict):
                n += arg_count_aux_i([con])
        count = max(count, n)
    return count


def arg_count_aux_i(list_):
    n = 0
    for arg in list_:
        if isinstance(arg, dict):
            if arg.get("con") is not None or arg.get("inh") is not None:
                n += 1
    return n


class SimpleContextRegenerateInterfaceFilesCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    state = IDLE
    first_error = True

    def reload_settings(self):
        super().reload_settings()
        self.context_paths = \
            utilities.get_setting_location(self, "ConTeXt_paths", default={})

    def run(
        self,
        paths=None,
        do_all=False,
        threaded=True,
        indent=2,
        overwrite=False,
        file_min=20000,
    ):
        paths = [] if paths is None else paths
        self.reload_settings()
        self.file_min = file_min
        self.indent = indent
        if self.state == IDLE:
            self.state = RUNNING

            def f():
                self.run_aux(
                    self.context_paths if do_all else paths, overwrite,
                )

            if threaded:
                threading.Thread(target=f).start()
            else:
                f()

    def run_aux(self, paths, overwrite):
        for path in paths:
            self.run_aux_i(path, overwrite)

    def run_aux_i(self, path, overwrite):
        if path in self.context_paths:
            path = self.context_paths[path]

        slug = files.file_as_slug(path)
        dir_ = os.path.join(
            sublime.packages_path(), "simple_ConTeXt", "interface", slug,
        )
        if overwrite:
            self.run_aux_ii(path, dir_, slug)
        else:
            self.run_aux_iii(path, dir_, slug)

        self.state = IDLE

    def run_aux_ii(self, path, dir_, slug):
        if os.path.exists(dir_):
            for f in os.listdir(dir_):
                os.remove(os.path.join(dir_, f))
        else:
            os.makedirs(dir_)
        self.run_aux_iv(path, dir_, slug)

    def run_aux_iii(self, path, dir_, slug):
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        commands = os.path.join(dir_, "_commands.json")
        if not os.path.exists(commands):
            try:
                self.run_aux_iv(path, dir_, slug)
            except OSError as e:
                if self.first_error:
                    self.first_error = False
                    text = (
                        '[simple_ConTeXt] failed to load interface, '
                        'encountered error: "{}"'
                    )
                    print(text.format(e))

    def run_aux_iv(self, path, dir_, slug):
        saver = save.InterfaceSaver(flags=self.flags, shell=self.shell)
        start_msg = (
            '[simple_ConTeXt] generating interface files (in folder "{}") '
            'for "{}"'
        )
        print(start_msg.format(slug, path))
        start_time = time.time()
        saver.save(
            path,
            modules=True,
            tolerant=True,
            quiet=True,
            prefix="[simple_ConTeXt] ",
            start_stop=False,
        )
        stop_msg = (
            '[simple_ConTeXt] finished generating interface files (for "{}") '
            'in {:.1f}s'
        )
        print(stop_msg.format(slug, time.time() - start_time))
        cmds = saver.encode()
        cache, key, size = {}, None, 0
        for name in sorted(cmds):
            key = name
            val = cmds[key]
            size += len(str(val))
            cache[key] = val
            if size > self.file_min:
                self.run_aux_v(
                    cache, os.path.join(dir_, "{}.json".format(key)),
                )
                cache.clear()
                size = 0
        if cache:
            self.run_aux_v(cache, os.path.join(dir_, "{}.json".format(key)))
        self.run_aux_v(
            sorted(
                [
                    "{}:{}".format(arg_count(desc), name)
                    for name, desc in cmds.items()
                ],
                key=lambda s: s.split(":", 1)[1],
            ),
            os.path.join(dir_, "_commands.json"),
        )

    def run_aux_v(self, data, file_):
        with open(file_, encoding="utf-8", mode="w") as f:
            json.dump(
                data,
                f,
                indent=self.indent,
                sort_keys=True,
                ensure_ascii=True,
            )
