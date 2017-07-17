# from . import interface_reading as reading
from . import utilities
# import html


class InterfaceWriter:
    def __init__(self):
        self.SYNTAX = '<syntax>{syntax}</syntax>'
        self.DOCSTRING = '<docstring>{docstring}</docstring>'
        self.FILE = '<file><a href="file:{file_dir}">{file}</a></file>'

    def render(self, *args, **kwargs):
        raw_text, raw_extra = self.render_aux(*args, **kwargs)
        if kwargs.get("pre_code", False):
            return [utilities.html_pre_code(s) for s in (raw_text, raw_extra)]
        else:
            return raw_text, raw_extra

    def render_aux(self, name, list_, files_cache, **kwargs):
        self.kwargs = kwargs
        self.name = name
        parts = []
        files = {}

        for alt in list_:
            content = alt.get("con")
            file = alt.get("fil")
            file_dir = files_cache.get(file)
            files[file] = file_dir
            sig = []

            if not content:
                syntax, docstring = self.render_aux_i([])
            elif isinstance(content, dict):
                syntax, docstring = self.render_aux_i([content])
            elif isinstance(content, list):
                syntax, docstring = self.render_aux_i(content)
            else:
                raise Exception('unexpected type "{}"'.format(type(content)))

            sig.append(self.SYNTAX.format(syntax=syntax))

            if len(docstring) > 0:
                sig.append(self.DOCSTRING.format(docstring=docstring))

            parts.append("\n\n".join(sig))

        if self.kwargs.get("show_source_files", False) and files:
            list_ = []
            for k in sorted(files):
                list_.append(self.FILE.format(file=k, file_dir=files[k]))
            extra = [" ".join(list_)]
        else:
            extra = []
        if self.kwargs.get("show_copy_pop_up", False):
            extra.append(
                '<clipboard>copy pop-up text: <a href="copy:plain">(plain)'
                '</a>, <a href="copy:html">(HTML)</a></clipboard>'
            )

        return "\n\n".join(parts), "\n\n".join(extra)

    def render_aux_i(self, list_):
        cs = "\\" + self.name
        self._syntax = [
            "<c>{}</c>".format(s) for s in [" " * len(cs), cs, " " * len(cs)]
        ]
        self._docstring = []
        self._n = 0

        for arg in list_:
            self.new_arg()

            self._content = arg.get("con")
            self._inherits = arg.get("inh")
            self._optional = arg.get("opt")
            self._rendering = arg.get("ren")
            self._len = len(utilities.html_unescape(
                utilities.html_strip_tags(self._rendering)
            ))

            if self._content is None and self._inherits is None:
                self.blank()
            else:
                self._n += 1
                self.syntax()
                self.docstring()

        self.clean_syntax()
        return "\n".join(self._syntax), "\n\n".join(self._docstring)

    def new_arg(self):
        for i in range(3):
            self._syntax[i] += " "

    def clean_syntax(self):
        for i in range(2, -1, -1):
            if not utilities.html_strip_tags(self._syntax[i]).rstrip():
                del self._syntax[i]

    def blank(self):
        self._syntax[0] += " " * self._len
        self._syntax[1] += self._rendering
        self._syntax[2] += " " * self._len

    def syntax(self):
        if self._optional:
            for i in range(3):
                self._syntax[i] += "<o>"
        self._syntax[0] += self.template(self._len + 7).format(
            "<n>{}</n>".format(self._n)
        )
        self._syntax[1] += self._rendering
        self._syntax[2] += self.template(self._len).format(
            "OPT" if self._optional else ""
        )
        if self._optional:
            for i in range(3):
                self._syntax[i] += "</o>"

    def docstring(self):
        if isinstance(self._content, str):
            self._docstring.append(self.docstring_str())
        elif isinstance(self._content, list):
            self._docstring.append(self.docstring_list())
        elif isinstance(self._content, dict):
            self._docstring.append(self.docstring_dict())

        if self._inherits:
            if self._content:
                self._docstring[-1] += (
                    "\n" +
                    self.guide(num=False) +
                    "<i>inherits:</i> <c>\\{}</c>".format(self._inherits)
                )
            else:
                self._docstring.append(
                    self.guide() +
                    "<i>inherits:</i> <c>\\{}</c>".format(self._inherits)
                )

    def docstring_str(self):
        return self.guide() + self._content

    def docstring_list(self):
        line_break = self.kwargs.get("line_break", 80)
        if isinstance(line_break, int):
            return self.docstring_list_break(line_break)
        else:
            return self.docstring_list_nobreak()

    def docstring_list_break(self, line_break):
        content = sorted(self._content.copy(), reverse=True)
        lines = []
        init = True

        while content:
            lines.append(self.guide(num=init))
            init, begin, space = False, True, True

            while content and space:
                s = content.pop()
                if begin:
                    lines[-1] += s
                    begin = False
                else:
                    len_ = len(utilities.html_strip_tags(lines[-1] + s)) + 1
                    if len_ > line_break:
                        space = False
                        content.append(s)
                    else:
                        lines[-1] += " " + s

        return "\n".join(lines)

    def docstring_list_nobreak(self):
        return self.guide() + " ".join(self._content)

    def docstring_dict(self):
        line_break = self.kwargs.get("line_break", 80)
        len_ = max(len(utilities.html_strip_tags(k)) for k in self._content)

        if isinstance(line_break, int):
            return self.docstring_dict_break(len_, line_break)
        else:
            return self.docstring_dict_nobreak(len_)

    def docstring_dict_break(self, len_, line_break):
        keys = sorted(self._content, reverse=True)
        lines = []
        init = True

        while keys:
            k = keys.pop()
            v = self._content[k]
            lines.append(self.assignments_guide(len_, key=k, num=init))
            init = False

            if isinstance(v, str):
                lines[-1] += " " + v
            elif isinstance(v, list):
                for s in v:
                    next_len = \
                        len(utilities.html_strip_tags(lines[-1] + s)) + 1
                    if next_len > line_break:
                        lines.append(self.assignments_guide(len_, num=init))
                        lines[-1] += " " + s
                    else:
                        lines[-1] += " " + s

        return "\n".join(lines)

    def docstring_dict_nobreak(self, len_):
        lines = []
        for i, k in enumerate(sorted(self._content)):
            v = self._content[k]
            lines.append(self.assignments_guide(len_, key=k, num=not i))
            lines[-1] += " " + " ".join(v) if isinstance(v, list) else v
        return "\n".join(lines)

    def template(self, t):
        return " {:^%s}" % (t - 1)

    def guide(self, num=True):
        if num:
            return "<n>{:<2}</n>  ".format(self._n)
        else:
            return "    "

    def assignments_guide(self, len_, key=None, num=True):
        start = self.guide(num=num)
        if key:
            return start + ("{:<%s} <e>=</e>" % len_).format(key)
        else:
            return start + (" " * (len_ + 2))
