import threading
import json
import os

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import files
from .scripts import save


IDLE = 0

RUNNING = 1


class SimpleContextRegenerateInterfaceFilesCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    state = IDLE
    first_error = True
    flags = files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

    def reload_settings_alt(self):
        self.reload_settings()
        self.context_paths = \
            utilities.get_setting_location(self, "ConTeXt_paths", default={})

    def run(
        self,
        paths=[],
        do_all=False,
        threaded=True,
        overwrite=False,
        file_min=20000,
    ):
        self.reload_settings_alt()
        self.file_min = file_min
        if self.state == IDLE:
            self.state = RUNNING

            def f():
                self.run_aux(
                    self.context_paths if do_all else paths, overwrite,
                )

            if threaded:
                thread = threading.Thread(target=f)
                thread.start()
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
            self.run_aux_ii(path, dir_)
        else:
            self.run_aux_iii(path, dir_)

        self.state = IDLE

    def run_aux_ii(self, path, dir_):
        if os.path.exists(dir_):
            for f in os.listdir(dir_):
                os.remove(os.path.join(dir_, f))
        else:
            os.makedirs(dir_)
        self.run_aux_iv(path, dir_)

    def run_aux_iii(self, path, dir_):
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        commands = os.path.join(dir_, "_commands.json")
        if not os.path.exists(commands):
            try:
                self.run_aux_iv(path, dir_)
            except OSError as e:
                if self.first_error:
                    self.first_error = False
                    text = 'failed to load interface, encountered error: "{}"'
                    print(text.format(e))

    def run_aux_iv(self, path, dir_):
        saver = save.InterfaceSaver(flags=self.flags)
        print("simple_ConTeXt: generating interface files...")
        saver.save(path, modules=True, tolerant=True)
        print("simple_ConTeXt: ...finished generating interface files")
        cmds = saver.encode()
        cache, key, size = {}, None, 0
        for name in sorted(cmds):
            key = name
            val = cmds[key]
            size += len(str(val))
            cache[key] = val
            if size > self.file_min:
                file_ = os.path.join(dir_, "{}.json".format(key))
                with open(file_, encoding="utf-8", mode="w") as f:
                    json.dump(cache, f)
                cache.clear()
                size = 0
        if cache:
            file_ = os.path.join(dir_, "{}.json".format(key))
            with open(file_, encoding="utf-8", mode="w") as f:
                json.dump(cache, f)
        file_ = os.path.join(dir_, "_commands.json")
        with open(file_, encoding="utf-8", mode="w") as f:
            json.dump(sorted(cmds), f)
