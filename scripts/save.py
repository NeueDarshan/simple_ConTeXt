import xml.etree.ElementTree as ET
import itertools
import html
import copy
import os

from . import utilities
from . import html_css
from . import files


NAMESPACE = {"cd": "http://www.pragma-ade.com/commands"}

UGLY_DEF_LOOKUP = {
    "instance-mathovertextextensible": "instance-mathoverextensible",
    "instance-mathundertextextensible": "instance-mathunderextensible",
}


class DefinitionNotFoundError(Exception):
    pass

class UnexpectedTagError(Exception):
    pass

class UnexpectedModeError(Exception):
    pass


class InterfaceSaver:
    def __init__(self, flags=0):
        self.method = {
            "range": ":",
            "factor": "*",
            "apply": self.escape("->"),
            "none": None,
        }
        self.delimiters = {
            "braces": "{}",
            "parentheses": "()",
            "default": "[]",
            "none": None,
        }
        self.defs = {}
        self.cmds = {}
        self.to_load = []
        self.flags = flags

    def parse(self, file_):
        return ET.parse(file_).getroot()

    def save(self, path, modules=True, tolerant=True, namespace=NAMESPACE):
        self.path = path
        self.namespace = namespace
        self.tolerant = tolerant
        self.load_definitions()
        self.load_commands(modules=modules)

    def load_definitions(self):
        """
        To handle resolves pointing to objects not yet defined, we simply do
        two passes. Of course, it would be better to handle the dependency
        graph in one pass, but this is simpler and seems to be fast enough.
        """
        self.load_definitions_aux()
        self.load_definitions_aux()

    def load_definitions_aux(self):
        file_ = files.locate(
            self.path, "i-common-definitions.xml", flags=self.flags,
        )
        if not file_:
            raise OSError('unable to locate "i-common-definitions.xml"')
        try:
            with open(file_, encoding="utf-8") as x:
                root = self.parse(x)
            for child in root:
                if self.tag_is(child, "interfacefile"):
                    self.load_definitions_aux_i(child.attrib.get("filename"))
                else:
                    raise UnexpectedTagError(
                        'unexpected tag "{}"'.format(child.tag)
                    )
        except (OSError, ET.ParseError, UnicodeDecodeError) as e:
            msg = 'in file "{}", {} error: "{}"'.format(file_, type(e), e)
            if self.tolerant:
                print(msg)
            else:
                raise type(e)(msg)

    def load_definitions_aux_i(self, filename):
        file_ = files.locate(self.path, filename, flags=self.flags)
        if not file_:
            raise OSError('unable to locate "{}"'.format(filename))
        try:
            with open(file_, encoding="utf-8") as x:
                root = self.parse(x)
            for child in root:
                self.do_define(child)
        except (OSError, ET.ParseError, UnicodeDecodeError) as e:
            msg = 'in file "{}", {} error: "{}"'.format(file_, type(e), e)
            if self.tolerant:
                print(msg)
            else:
                raise type(e)(msg)

    def load_commands(self, modules=True):
        self.to_load = set()

        main = files.locate(self.path, "i-context.xml", flags=self.flags)
        if main:
            dir_ = os.path.split(main)[0]
            for file_ in os.listdir(dir_):
                if self.load_commands_aux(file_):
                    self.to_load.add(os.path.join(dir_, file_))

        if modules:
            # Let's use \type{t-rst.xml} as a smoking gun.
            alt = files.locate(self.path, "t-rst.xml", flags=self.flags)
            if alt:
                dir_ = os.path.split(alt)[0]
                for file_ in os.listdir(dir_):
                    if self.load_commands_aux(file_):
                        self.to_load.add(os.path.join(dir_, file_))

        self.load_commands_aux_i()

    def load_commands_aux(self, file_):
        return all([
            file_.endswith(".xml"),
            not file_.startswith("i-common"),
            not file_.startswith("i-context"),
            file_ != "context-en.xml",
        ])

    def load_commands_aux_i(self):
        for file_ in self.to_load:
            try:
                with open(file_, encoding="utf-8") as x:
                    root = self.parse(x)
                for child in root:
                    if self.tag_is(child, "command"):
                        self.do_command(child)
                    elif self.tag_is(child, "define"):
                        self.do_define(child)
                    else:
                        raise UnexpectedTagError(
                            'in file "{}", unexpected tag "{}"'.format(
                                file_, child.tag,
                            )
                        )
            except (OSError, ET.ParseError, UnicodeDecodeError) as e:
                msg = 'in file "{}", {} error: "{}"'.format(file_, type(e), e)
                if self.tolerant:
                    print(msg)
                else:
                    raise type(e)(msg)

    def do_define(self, node):
        name = node.attrib["name"]
        obj = []
        for child in node:
            if self.tag_is(child, "constant"):
                obj.append(self.do_constant(child))
            elif self.tag_is(child, "inherit"):
                obj.append(
                    "<inh>inherits:</inh> " +
                    html_css.control_sequence(self.do_inherit(child))
                )
            elif self.tag_is(child, "keywords"):
                obj.append(self.do_keywords(child))
            elif self.tag_is(child, "assignments"):
                obj.append(self.do_assignments(child))
            else:
                message = 'unexpected tag, attrib: "{}", tag: "{}"'
                raise UnexpectedTagError(
                    message.format(child.attrib, child.tag)
                )
        self.add_def(name, self.flatten(obj))

    def do_command(self, node):
        instances = self.find(node, "instances")
        sequence = self.find(node, "sequence")
        name = node.attrib["name"]

        # Should we try to handle control symbols? Let's ignore them at the
        # moment.
        if not name.isalpha():
            return

        template = ""
        keys = []
        for child in sequence:
            if self.tag_is(child, "string", "constant", "variable"):
                template += child.attrib["value"]
            elif self.tag_is(child, "instance"):
                template += "{}"
                keys.append(child.attrib["value"])
            else:
                raise UnexpectedTagError(
                    'sequence: unexpected tag "{}"'.format(child.tag)
                )
        if not template:
            template = "{}"

        for instance in instances:
            if self.tag_is(instance, "constant"):
                keys.append(instance.attrib["value"])
            elif self.tag_is(instance, "resolve"):
                def_ = self.get_def(instance.attrib["name"])
                if isinstance(def_, list):
                    for d in def_:
                        keys.append(d)
                else:
                    keys.append(def_)
            else:
                raise UnexpectedTagError(
                    'sequence: unexpected tag "{}"'.format(instance.tag)
                )
        if not keys:
            keys.append(name)

        for key in set(keys):
            if key:
                text = template.format(key)
                if text == key * 2:
                    text = key
                self.do_command_aux(text, node)

    def do_command_aux(self, name, node):
        attrib = node.attrib

        if attrib.get("type") == "environment":
            begin = self.clean_name(attrib.get("begin", "start") + name)
            end = self.clean_name(attrib.get("end", "stop") + name)
            node_copy = copy.deepcopy(node)
            args = self.find(node_copy, "arguments")
            if args:
                args.append(self.dots_node())
                args.append(self.delim_node(end))
            else:
                node_copy.append(self.tail_args_node(end))
            self.do_command_aux_i(begin, node_copy)
            # We could signal primitives in a better way. For now they are
            # implicitly signalled by setting file equal to \type{None}.
            self.do_command_aux_i(end, self.empty_node(attrib.get("file")))
        else:
            self.do_command_aux_i(self.clean_name(name), node)

    def do_command_aux_i(self, name, node):
        arguments = self.find(node, "arguments")
        handlers = {
            "angles": self.do_angles,
            "apply": self.do_apply,
            "assignments": self.do_assignments,
            "content": self.do_content,
            "csname": self.do_csname,
            "delimiter": self.do_delimiter,
            # This one is an addition of ours for convenience.
            "dotsdelimiter": self.do_dots_delimiter,
            "index": self.do_index,
            "keywords": self.do_keywords,
            "position": self.do_position,
            "resolve": self.do_resolve,
            "template": self.do_template,
            "text": self.do_text,
            "triplet": self.do_triplet,
        }
        content = []
        for child in arguments:
            if self.tag_is(child, *handlers):
                content.append(handlers[self.raw_tag(child)](child))
            else:
                message = \
                    'unexpected tag, name: "{}", attrib: "{}", tag: "{}"'
                raise UnexpectedTagError(
                    message.format(name, child.attrib, child.tag)
                )
        self.add_cmd(
            name,
            {"con": self.flatten(content), "fil": node.attrib.get("file")},
        )

    def do_constant(self, node):
        attrib = node.attrib
        value = self.transform(attrib.get("value", ""))
        name = self.transform(attrib.get("name", ""))
        type_ = self.transform(attrib.get("type", ""))
        prefix = self.transform(attrib.get("prefix", ""))
        method = self.method.get(attrib.get("method", "none"))
        if self.is_true(attrib.get("default")):
            start, stop = "<val>", "</val>"
        else:
            start, stop = "", ""
        return (
            start + prefix + (method if method else "") + type_ + name +
            value + stop
        )

    def do_keywords(self, node):
        inherits = []
        content = []
        for child in node:
            if self.tag_is(child, "constant"):
                content.append(self.do_constant(child))
            elif self.tag_is(child, "resolve"):
                content.append(self.do_resolve(child))
            elif self.tag_is(child, "inherit"):
                inherits.append(self.do_inherit(child))
            elif self.tag_is(child, "content"):
                inherits.append(self.do_content(child))
            else:
                message = 'unexpected tag, attrib: "{}", tag: "{}"'
                raise UnexpectedTagError(
                    message.format(child.attrib, child.tag)
                )
        return {
            "con": self.flatten(content),
            "ren": self.render("keywords", node.attrib),
            "inh": self.flatten(inherits),
            "opt": self.is_true(node.attrib.get("optional")),
        }

    def do_assignments(self, node):
        inherits = []
        content = {}
        for child in node:
            name = self.transform(child.attrib["name"])
            if self.tag_is(child, "parameter"):
                content[name] = self.do_parameter(child)
            elif self.tag_is(child, "inherit"):
                inherits.append(self.do_inherit(child))
            else:
                message = 'unexpected tag, attrib: "{}", tag: "{}"'
                raise UnexpectedTagError(
                    message.format(child.attrib, child.tag)
                )
        return {
            "con": content if content else None,
            "ren": self.render("assignments", node.attrib),
            "inh": self.flatten(inherits),
            "opt": self.is_true(node.attrib.get("optional")),
        }

    def do_parameter(self, node):
        content = []
        for child in node:
            if self.tag_is(child, "constant"):
                content.append(self.do_constant(child))
            elif self.tag_is(child, "resolve"):
                content.append(self.do_resolve(child))
            elif self.tag_is(child, "inherit"):
                content.append(
                    "<inh>inherits:</inh> " +
                    html_css.control_sequence(self.do_inherit(child))
                )
            else:
                message = 'unexpected tag, attrib: "{}", tag: "{}"'
                raise UnexpectedTagError(
                    message.format(child.attrib, child.tag)
                )
        return self.flatten(content)

    def do_delimiter(self, node):
        return {
            "con": None,
            "inh": None,
            "opt": False,
            "ren": self.render("delimiter", node.attrib),
        }

    def do_dots_delimiter(self, node):
        return {"con": None, "inh": None, "opt": False, "ren": "..."}

    def do_angles(self, node):
        return self.do_generic("ANGLES", "angles", node.attrib)

    def do_template(self, node):
        return self.do_generic("TEMPLATE", "template", node.attrib)

    def do_apply(self, node):
        return self.do_generic("APPLY", "apply", node.attrib)

    def do_text(self, node):
        return self.do_generic("TEXT", "text", node.attrib)

    def do_index(self, node):
        return self.do_generic("INDEX", "index", node.attrib)

    def do_position(self, node):
        return self.do_generic("POSITION", "position", node.attrib)

    def do_triplet(self, node):
        return self.do_generic("TRIPLET", "triplet", node.attrib)

    def do_csname(self, node):
        return self.do_generic("CSNAME", "csname", node.attrib)

    def do_content(self, node):
        return self.do_generic("CONTENT", "content", node.attrib)

    def do_generic(self, type_, render, attrib):
        return {
            "con": "<typ>{}</typ>".format(self.escape(type_)),
            "inh": None,
            "opt": self.is_true(attrib.get("optional")),
            "ren": self.render(render, attrib),
        }

    def do_resolve(self, node):
        name = node.attrib["name"]
        return self.defs.get(name)

    def do_inherit(self, node):
        return node.attrib["name"]

    def render(self, mode, attrib):
        is_list = self.is_true(attrib.get("list"))
        delims = self.delimiters.get(attrib.get("delimiters", "default"), "[]")
        punct = "<pun>{}</pun>"
        if delims:
            start, stop = punct.format(delims[0]), punct.format(delims[1])
        else:
            start, stop = "", ""

        if mode == "keywords":
            middle = "...<com>,</com>..." if is_list else "..."
            return start + middle + stop
        elif mode == "assignments":
            middle = (
                "..<com>,</com><key>..</key><equ>=</equ>..<com>,</com>.."
                if is_list else "<key>..</key><equ>=</equ>.."
            )
            return start + middle + stop
        elif mode == "triplet":
            middle = \
                "..<com>,</com>x:y:z<com>,</com>.." if is_list else "x:y:z"
            return start + middle + stop
        elif mode == "index":
            return start + "..+...+.." + stop
        elif mode == "template":
            return start + "|...|" + stop
        elif mode == "angles":
            return "<pun>{}</pun>...<pun>{}</pun>".format(
                self.escape("<<"), self.escape(">>")
            )
        elif mode == "apply":
            if is_list:
                temp = "..<com>,</com><key>..</key><equ>{}</equ>..,.."
                middle = temp.format(self.escape("=>"))
            else:
                middle = \
                    "<key>..</key><equ>{}</equ>..".format(self.escape("=>"))
            return start + middle + stop
        elif mode == "position":
            middle = "...<com>,</com>..." if is_list else "..."
            return punct.format("(") + middle + punct.format(")")
        elif mode == "csname":
            return html_css.control_sequence("...")
        elif mode in ["content", "text"]:
            return "<pun>{</pun>...<pun>}</pun>"
        elif mode == "delimiter":
            return html_css.control_sequence(self.escape(attrib["name"]))
        else:
            msg = 'unexpected mode, mode: "{}", attrib: "{}"'
            if self.tolerant:
                print(msg.format(mode, attrib))
                return None
            else:
                raise UnexpectedModeError(msg.format(mode, attrib))

    # def signal_primitive(self):
    #     pass

    def is_true(self, val):
        return val == "yes"

    def flatten(self, obj):
        return obj
        # if not obj:
        #     return None
        # elif len(obj) == 1:
        #     return obj[0]
        # if all(
        #     isinstance(e, str) or (
        #         isinstance(e, list) and all(isinstance(s, str) for s in e)
        #     )
        #     for e in obj
        # ):
        #     res = []
        #     for e in obj:
        #         if isinstance(e, str):
        #             res.append(e)
        #         else:
        #             res += e
        #     return res
        # return obj

    def transform(self, text, escape=True):
        f = self.escape if escape else self.identity
        if text == "cd:sign":
            return f("[+-]")
        elif text.startswith("cd:"):
            return "<typ>" + f(text[3:].upper()) + "</typ>"
        return f(text)

    def escape(self, text):
        return html.escape(text, quote=False)

    def identity(self, text):
        return text

    def clean_name(self, text):
        return text.replace("​", "")  # remove zero||width whitespace

    def empty_node(self, file_):
        return ET.fromstring((
            '<cd:command xmlns:cd="http://www.pragma-ade.com/commands" '
            'file="{}" />'
        ).format(file_))

    def dots_node(self):
        return ET.fromstring(
            '<cd:dotsdelimiter xmlns:cd="http://www.pragma-ade.com'
            '/commands" />'
        )

    def delim_node(self, name):
        return ET.fromstring((
            '<cd:delimiter xmlns:cd="http://www.pragma-ade.com/commands" '
            'name="{}" />'
        ).format(name))

    def tail_args_node(self, name):
        return ET.fromstring((
            '<cd:arguments xmlns:cd="http://www.pragma-ade.com/commands">'
            '<cd:dotsdelimiter xmlns:cd="http://www.pragma-ade.com/commands" '
            '/>'
            '<cd:delimiter xmlns:cd="http://www.pragma-ade.com/commands" '
            'name="{}" />'
            '</cd:arguments>'
        ).format(name))

    def find(self, node, query):
        result = node.find(self.get_tag(query))
        return result if result else []

    def findall(self, node, query):
        result = node.findall(self.get_tag(query))
        return result if result else []

    def tag_is(self, node, *tags):
        return node.tag in [self.get_tag(tag) for tag in tags]

    def get_tag(self, tag):
        return "{%s}%s" % (self.namespace.get("cd"), tag)

    def raw_tag(self, node):
        return node.tag.rsplit("}", maxsplit=1)[-1]

    def add_def(self, name, obj):
        self.defs[name] = obj

    def get_def(self, name):
        if name in self.defs:
            return self.defs[name]
        for key, val in UGLY_DEF_LOOKUP.items():
            if name == key:
                return self.get_def(val)
        message = "unexpected resolve, could not find '{}'"
        raise DefinitionNotFoundError(message.format(name))

    def add_cmd(self, name, obj):
        if name in self.cmds:
            self.cmds[name].append(obj)
        else:
            self.cmds[name] = [obj]

    def simplify(self):
        for name in self.cmds:
            self.cmds[name] = self.simplify_aux(self.cmds[name])

    def simplify_aux(self, vars_):
        new = []
        for v in vars_:
            if not any(d == v for d in new):
                new.append(v)
        return self.simplify_aux_i(new)

    def simplify_aux_i(self, vars_):
        if len(vars_) <= 1:
            return vars_
        var_copy = copy.deepcopy(vars_)

        done = False
        while not done:
            done = True
            for pair in itertools.permutations(
                [(n, entry) for n, entry in enumerate(var_copy)], 2,
            ):
                i, master = pair[0]
                j, other = pair[1]
                redundant = False
                for master_var in self.iter_mand_to_opt(master):
                    if self.is_copy_without_opt(other, master_var):
                        redundant = True
                        var_copy[i] = master_var
                        del var_copy[j]
                        break
                if redundant:
                    done = False
                    break

        return var_copy

    def iter_mand_to_opt(self, syntax):
        if syntax["con"] is None:
            yield syntax
            return
        if not isinstance(syntax["con"], list):
            syntax["con"] = [syntax["con"]]
        mand_ind = [
            i for i in range(len(syntax["con"])) if not syntax["con"][i]["opt"]
        ]
        copy_ = copy.deepcopy(syntax)
        for comb in utilities.iter_power_set(mand_ind):
            for i in mand_ind:
                copy_["con"][i]["opt"] = bool(i in comb)
            yield copy_

    def is_copy_without_opt(self, other, master):
        return any(
            reduced == other for reduced in self.iter_without_opt(master)
        )

    def iter_without_opt(self, syntax):
        if syntax["con"] is None:
            yield syntax
            raise StopIteration
        if not isinstance(syntax["con"], list):
            syntax["con"] = [syntax["con"]]
        len_ = len(syntax["con"])
        opt_ind = [
            i for i in range(len_) if syntax["con"][i]["opt"]
        ]
        mand_ind = [i for i in range(len_) if i not in opt_ind]

        for comb in utilities.iter_power_set(opt_ind):
            ind = set(comb)
            ind.update(mand_ind)
            yield [syntax["con"][i] for i in sorted(ind)]

    def encode(self):
        self.simplify()
        return self.cmds
