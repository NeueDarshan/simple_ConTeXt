from . import html_css


def nice_sorted(list_, reverse=False):
    list_ = sorted(
        [l for l in list_ if l is not None], key=html_css.strip_tags
    )
    inherits, upper, mixed, lower = [], [], [], []
    for e in list_:
        raw = html_css.strip_tags(e)
        if raw.startswith("inherits"):
            inherits.append(e)
        elif raw.isupper():
            upper.append(e)
        elif any(c.isupper() for c in raw):
            mixed.append(e)
        else:
            lower.append(e)
    if reverse:
        return (
            list(reversed(inherits)) + list(reversed(upper)) +
            list(reversed(mixed)) + list(reversed(lower))
        )
    else:
        return lower + mixed + upper + inherits


class InterfaceLoader:
    def __init__(self):
        self.syntax = '<syntax>{syntax}</syntax>'
        self.docstring = '<docstring>{docstring}</docstring>'
        self.file = '<file><a href="file:{file}">{file}</a></file>'

    def load(self, *args, **kwargs):
        raw = self.render(*args, **kwargs)
        if kwargs.get("protect_space", False):
            return [html_css.protect_space(s) for s in raw]
        else:
            return raw

    def render(self, name, list_, **kwargs):
        self.kwargs = kwargs
        self.name = name
        parts = []
        files = set()

        for alt in list_:
            content = alt.get("con")
            files.add(alt.get("fil"))
            sig = []

            if not content:
                syntax, docstring = self.render_aux([])
            elif isinstance(content, dict):
                syntax, docstring = self.render_aux([content])
            elif isinstance(content, list):
                syntax, docstring = self.render_aux(content)
            else:
                raise Exception('unexpected type "{}"'.format(type(content)))

            sig.append(self.syntax.format(syntax=syntax))

            if len(docstring) > 0:
                sig.append(self.docstring.format(docstring=docstring))

            parts.append("\n\n".join(sig))

        if self.kwargs.get("show_source_files", False) and files:
            source = " ".join(self.file.format(file=k) for k in sorted(files))
        else:
            source = ""
        if self.kwargs.get("show_copy_pop_up", False):
            copy = (
                '<clipboard>copy pop-up text: <a href="copy:plain">(plain)'
                '</a>, <a href="copy:html">(HTML)</a></clipboard>'
            )
        else:
            copy = ""

        return ["\n\n".join(parts), source, copy]

    def render_aux(self, list_):
        self._syntax = [
            " " * (len(self.name) + 1),
            "<l>\\</l><c>{}</c>".format(self.name),
            " " * (len(self.name) + 1)
        ]
        self._docstring = []
        self._n = 0

        for arg in list_:
            if arg:
                self.new_arg()

                self._content = arg.get("con")
                self._inherits = arg.get("inh")
                self._optional = arg.get("opt")
                self._rendering = arg.get("ren")
                self._len = len(html_css.unescape(
                    html_css.strip_tags(self._rendering)
                ))

                if self._content is None and self._inherits is None:
                    self.blank()
                else:
                    self._n += 1
                    self.do_syntax()
                    self.do_docstring()

        self.clean_syntax()
        return "\n".join(self._syntax), "\n\n".join(self._docstring)

    def new_arg(self):
        for i in range(3):
            self._syntax[i] += " "

    def clean_syntax(self):
        for i in range(2, -1, -1):
            if not html_css.strip_tags(self._syntax[i]).rstrip():
                del self._syntax[i]

    def blank(self):
        self._syntax[0] += " " * self._len
        self._syntax[1] += self._rendering
        self._syntax[2] += " " * self._len

    def do_syntax(self):
        if self._optional:
            for i in range(3):
                self._syntax[i] += "<o>"
        self._syntax[0] += self.template(self._len + 7).format(
            "<n>{}</n>".format(self._n)
        )
        self._syntax[1] += self._rendering
        self._syntax[2] += self.template(self._len, min=3).format(
            "OPT" if self._optional else ""
        )
        if self._optional:
            for i in range(3):
                self._syntax[i] += "</o>"

    def do_docstring(self):
        if isinstance(self._content, str):
            self._docstring.append(self.docstring_str())
        elif isinstance(self._content, list):
            self._docstring.append(self.docstring_list())
        elif isinstance(self._content, dict):
            self._docstring.append(self.docstring_dict())

        if self._inherits:
            if isinstance(self._inherits, list):
                inherits = "<h>inherits:</h> " + ", ".join(
                    "<l>\\</l><c>{}</c>".format(i) for i in self._inherits
                )
            else:
                inherits = (
                    "<h>inherits:</h> " +
                    "<l>\\</l><c>{}</c>".format(self._inherits)
                )
            if self._content:
                self._docstring[-1] += "\n" + self.guide(num=False) + inherits
            else:
                self._docstring.append(self.guide() + inherits)

    def docstring_str(self):
        return self.guide() + self._content

    def docstring_list(self):
        line_break = self.kwargs.get("line_break", 80)
        if isinstance(line_break, int):
            return self.docstring_list_break(line_break)
        else:
            return self.docstring_list_nobreak()

    def docstring_list_break(self, line_break):
        content = nice_sorted(self._content.copy(), reverse=True)
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
                    len_ = len(html_css.strip_tags(lines[-1] + s)) + 1
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
        len_ = max(len(html_css.strip_tags(k)) for k in self._content)

        if isinstance(line_break, int):
            return self.docstring_dict_break(len_, line_break)
        else:
            return self.docstring_dict_nobreak(len_)

    def docstring_dict_break(self, len_, line_break):
        keys = nice_sorted(self._content, reverse=True)
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
                for s in nice_sorted(v):
                    next_len = \
                        len(html_css.strip_tags(lines[-1] + s)) + 1
                    if next_len > line_break:
                        lines.append(self.assignments_guide(len_, num=init))
                        lines[-1] += " " + s
                    else:
                        lines[-1] += " " + s

        return "\n".join(lines)

    def docstring_dict_nobreak(self, len_):
        lines = []
        for i, k in enumerate(nice_sorted(self._content)):
            v = self._content[k]
            lines.append(self.assignments_guide(len_, key=k, num=not i) + " ")
            lines[-1] += " ".join(nice_sorted(v)) if isinstance(v, list) else v
        return "\n".join(lines)

    def template(self, t, min=None):
        if not min or t > min:
            return " {:^%s}" % (t - 1)
        else:
            return "{:^%s}" % t

    def guide(self, num=True):
        if num:
            return "<n>{:<2}</n>  ".format(self._n)
        else:
            return "    "

    def assignments_guide(self, len_, key=None, num=True):
        start = self.guide(num=num)
        if key:
            len_ += len(key) - len(html_css.strip_tags(key))
            return start + ("<k>{:<%s}</k> <e>=</e>" % len_).format(key)
        else:
            return start + (" " * (len_ + 2))
