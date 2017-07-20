import xml.etree.ElementTree as ET
import collections
import itertools
import html
import copy
from . import utilities


NAMESPACE = {"cd": "http://www.pragma-ade.com/commands"}


class InterfaceLoader:
    def __init__(self):
        self.METHOD = {
            "range": ":",
            "factor": "*",
            "apply": self.escape("->"),
            "none": None,
        }
        self.DELIMITERS = {
            "braces": "{}",
            "parentheses": "()",
            "default": "[]",
            "none": None,
        }
        self.defs = {}
        self.cmds = {}
        self.to_load = collections.deque()

    def load(self, path, passes=3, modules=True, namespace=NAMESPACE):
        self.path = path
        self.namespace = namespace
        if passes >= 1:
            self.first_pass(modules=modules)
        if passes >= 2:
            self.second_pass(modules=modules)
        if passes >= 3:
            self.third_pass(modules=modules)
        self.simplify()

    def first_pass(self, modules=True):
        self.do_define = self._do_define
        self.do_resolve = self._null
        self.do_command = self._null
        self.pre_load(modules=modules)
        self.load_aux()

    def second_pass(self, modules=True):
        self.do_resolve = self._do_resolve
        self.pre_load(modules=modules)
        self.load_aux()

    def third_pass(self, modules=True):
        self.do_define = self._null
        self.do_command = self._do_command
        self.pre_load(modules=modules)
        self.load_aux()

    def pre_load(self, modules=True):
        self.to_load.clear()
        if modules:
            self.to_load.append("i-context-modules.xml")
        self.to_load.append("i-context.xml")

    def _null(self, *args, **kwargs):
        return

    def load_aux(self):
        while len(self.to_load) > 0:
            name = self.to_load.pop()
            f = utilities.locate(self.path, name)
            if not f:
                print('load > error > unable to locate "{}"'.format(name))
                continue
            try:
                with open(f) as x:
                    tree = ET.parse(x)
                    root = tree.getroot()
                for child in root:
                    if self.tag_is(child, "interfacefile"):
                        filename = child.attrib.get("filename")
                        if filename:
                            self.to_load.append(filename)
                            self.load_aux()
                        else:
                            print("load > error > no filename attrib")
                    elif self.tag_is(child, "define"):
                        self.do_define(child)
                    elif self.tag_is(child, "command"):
                        self.do_command(child)
                    else:
                        print(
                            'load > error > unexpected tag "{}"'
                            .format(child.tag)
                        )
            except FileNotFoundError as e:
                print('load > error > IO/OS Error "{}"'.format(e))
            except ET.ParseError as e:
                print(
                    'load > error > ET Parse Error "{}"'.format(e)
                )

    def _do_define(self, node):
        name = node.attrib["name"]
        obj = []
        for child in node:
            if self.tag_is(child, "constant"):
                obj.append(self.do_constant(child))
            elif self.tag_is(child, "inherit"):
                obj.append(
                    "<i>inherits:</i> <c>\\{}</c>".format(
                        self.do_inherit(child)
                    )
                )
            elif self.tag_is(child, "keywords"):
                obj.append(self.do_keywords(child))
            elif self.tag_is(child, "assignments"):
                obj.append(self.do_assignments(child))
            else:
                message = (
                    'define > error > unexpected tag\ndefine > details >'
                    'attrib: "{}", tag: "{}"'
                )
                print(message.format(child.attrib, child.tag))
        self.add_def(name, self.flatten(obj))

    def _do_command(self, node):
        instances = self.find(node, "instances")
        sequence = self.find(node, "sequence")
        name = node.attrib["name"]

        template = ""
        keys = []
        for child in sequence:
            if self.tag_is(child, "string", "constant", "variable"):
                template += child.attrib["value"]
            elif self.tag_is(child, "instance"):
                template += "{}"
                keys.append(child.attrib["value"])
            else:
                print(
                    'do_command > error > sequence: unexpected tag "{}"'
                    .format(child.tag)
                )
        if len(template) == 0:
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
                print(
                    'do_command > error > sequence: unexpected tag "{}"'
                    .format(instance.tag)
                )
        if len(keys) == 0:
            keys.append(name)

        for key in set(keys):
            text = template.format(key)
            if text == key * 2:
                text = key
            self.do_command_aux(text, node)

    def do_command_aux(self, name, node):
        attrib = node.attrib
        file = attrib.get("file")
        if attrib.get("type") == "environment":
            begin = attrib.get("begin", "start") + name
            end = attrib.get("end", "stop") + name
            node_copy = copy.deepcopy(node)
            self.find(node_copy, "arguments").append(self.dots_node())
            self.find(node_copy, "arguments").append(self.delim_node(end))
            self.do_command_aux_i(begin, node_copy)
            self.do_command_aux_i(end, self.empty_node(file))
        else:
            self.do_command_aux_i(name, node)

    def do_command_aux_i(self, name, node):
        arguments = self.find(node, "arguments")
        handlers = {
            "assignments": self.do_assignments,
            "keywords": self.do_keywords,
            "resolve": self.do_resolve,
            "csname": self.do_csname,
            "content": self.do_content,
            "delimiter": self.do_delimiter,
            "emptydelimiter": self.do_empty_delimiter,
            "triplet": self.do_triplet,
            "position": self.do_position,
            "index": self.do_index,
            "text": self.do_text,
            "apply": self.do_apply,
            "template": self.do_template,
            "angles": self.do_angles,
        }
        content = []
        for child in arguments:
            if self.tag_is(child, *handlers):
                content.append(handlers[self.raw_tag(child)](child))
            else:
                message = (
                    'do_command > error > unexpected tag\ndo_command >'
                    'details > name: "{}", attrib: "{}", tag: "{}"'
                )
                print(message.format(name, child.attrib, child.tag))
        self.add_cmd(
            name,
            {"con": self.flatten(content), "fil": node.attrib.get("file")}
        )

    def do_constant(self, node):
        attrib = node.attrib
        value = self.transform(attrib.get("value", ""))
        name = self.transform(attrib.get("name", ""))
        type_ = self.transform(attrib.get("type", ""))
        prefix = self.transform(attrib.get("prefix", ""))
        method = self.METHOD.get(attrib.get("method", "none"))
        if self.is_true(attrib.get("default")):
            start, stop = "<d>", "</d>"
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
            else:
                message = (
                    'do_keywords > error > unexpected tag\ndo_keywords > '
                    'details > attrib: "{}", tag: "{}"'
                )
                print(message.format(child.attrib, child.tag))
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
                message = (
                    'do_assignments > error > unexpected tag\ndo_assignments '
                    '> details > attrib: "{}", tag: "{}"'
                )
                print(message.format(child.attrib, child.tag))
        return {
            "con": content if len(content) > 0 else None,
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
                content.append("<i>inherits:</i> <c>\\{}</c>".format(
                    self.do_inherit(child)
                ))
            else:
                message = (
                    'do_parameter > error > unexpected tag\ndo_parameter > '
                    'details > attrib: "{}", tag: "{}"'
                )
                print(message.format(child.attrib, child.tag))
        return self.flatten(content)

    def do_delimiter(self, node):
        return {
            "con": None,
            "inh": None,
            "opt": False,
            "ren": self.render("delimiter", node.attrib),
        }

    def do_empty_delimiter(self, node):
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
            "con": "<t>{}</t>".format(self.escape(type_)),
            "inh": None,
            "opt": self.is_true(attrib.get("optional")),
            "ren": self.render(render, attrib),
        }

    def _do_resolve(self, node):
        name = node.attrib["name"]
        return self.defs.get(name)

    def do_inherit(self, node):
        return node.attrib["name"]

    def render(self, mode, attrib):
        is_list = self.is_true(attrib.get("list"))
        delims = self.DELIMITERS.get(attrib.get("delimiters", "default"), "[]")
        if delims:
            start, stop = delims[0], delims[1]
        else:
            start, stop = "", ""

        if mode == "keywords":
            middle = "...,..." if is_list else "..."
            return start + middle + stop
        elif mode == "assignments":
            middle = "..,..=..,.." if is_list else "..=.."
            return start + middle + stop
        elif mode == "triplet":
            middle = "..,x:y:z,.." if is_list else "x:y:z"
            return start + middle + stop
        elif mode == "index":
            return start + "..+...+.." + stop
        elif mode == "template":
            return start + "|...|" + stop
        elif mode == "angles":
            return self.escape("<<...>>")
        elif mode == "apply":
            middle = "..,..=>..,.." if is_list else "..=>.."
            return start + self.escape(middle) + stop
        elif mode == "position":
            middle = "...,..." if is_list else "..."
            return "(" + middle + ")"
        elif mode == "csname":
            return "<c>\\...</c>"
        elif mode in ["content", "text"]:
            return "{...}"
        elif mode == "delimiter":
            return "<c>\\{}</c>".format(self.escape(attrib["name"]))
        else:
            message = (
                'render > error > unexpected mode\nrender > '
                'details > mode: "{}", attrib: "{}"'
            )
            print(message.format(mode, attrib))

    def is_true(self, val):
        return val == "yes"

    def flatten(self, obj):
        if len(obj) == 0:
            return None
        elif len(obj) == 1:
            return obj[0]
        else:
            if all(
                isinstance(e, str) or (
                    isinstance(e, list) and all(isinstance(s, str) for s in e)
                )
                for e in obj
            ):
                res = []
                for e in obj:
                    if isinstance(e, str):
                        res.append(e)
                    else:
                        res += e
                return res
            else:
                return obj

    def transform(self, s, escape=True):
        f = self.escape if escape else self.identity
        if s == "cd:sign":
            return f("[+-]")
        elif s.startswith("cd:"):
            return "<t>" + f(s[3:].upper()) + "</t>"
        else:
            return f(s)

    def escape(self, s):
        return html.escape(s, quote=False)

    def identity(self, s):
        return s

    def empty_node(self, file):
        return ET.fromstring(
            '<cd:command xmlns:cd="http://www.pragma-ade.com/commands" ' +
            'file="{}" />'.format(file)
        )

    def dots_node(self):
        return ET.fromstring(
            '<cd:emptydelimiter xmlns:cd="http://www.pragma-ade.com' +
            '/commands" />'
        )

    def delim_node(self, name):
        return ET.fromstring(
            '<cd:delimiter xmlns:cd="http://www.pragma-ade.com/commands" ' +
            'name="{}" />'.format(name)
        )

    def find(self, node, query):
        result = node.find(self.get_tag(query))
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
        return self.defs[name]

    def add_cmd(self, name, obj):
        if name not in self.cmds:
            self.cmds[name] = [obj]
        else:
            self.cmds[name].append(obj)

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
        len_ = len(vars_)
        if len_ <= 1:
            return vars_
        var_copy = copy.deepcopy(vars_)

        done = False
        while not done:
            done = True
            for pair in itertools.permutations(
                [(n, entry) for n, entry in enumerate(var_copy)], 2
            ):
                i, master = pair[0]
                j, other = pair[1]
                redundant = False
                for master_var in self._iter_mand_to_opt(master):
                    if self._is_copy_without_opt(other, master_var):
                        redundant = True
                        var_copy[i] = master_var
                        del var_copy[j]
                        break
                if redundant:
                    done = False
                    break

        return var_copy

    def _iter_mand_to_opt(self, syntax):
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

    def _is_copy_without_opt(self, other, master):
        return any(
            reduced == other for reduced in self._iter_without_opt(master)
        )

    def _iter_without_opt(self, syntax):
        if syntax["con"] is None:
            yield syntax
            return
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
        files = {}
        for name, cmd in self.cmds.items():
            for alt in cmd:
                name = alt.get("fil")
                if name not in files:
                    path = utilities.locate(self.path, name)
                    files[name] = path
        return {"details": self.cmds, "files": files}
