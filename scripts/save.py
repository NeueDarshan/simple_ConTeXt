import copy
import html
import os
import xml.etree.ElementTree as ET

from typing import (  # noqa
    Any, Dict, Iterable, List, Optional, Set, TextIO, Tuple, TypeVar, Union
)

from . import files
from . import html_css
from . import utilities


T = TypeVar("T")

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
    delimiters = {
        "braces": "{}",
        "parentheses": "()",
        "default": "[]",
        "none": None,
    }
    defs = {}  # type: Dict[str, Any]
    cmds = {}  # type: Dict[str, Any]
    to_load = set()  # type: Set[str]

    def __init__(self, flags: int = 0, shell: bool = False) -> None:
        self.flags = flags
        self.shell = shell
        self.method = {
            "range": ":",
            "factor": "*",
            "apply": self.escape("->"),
            "none": None,
        }

    def parse(self, file_: Union[str, TextIO]) -> ET.Element:
        return ET.parse(file_).getroot()

    def save(
        self,
        path: str,
        modules: bool = True,
        tolerant: bool = True,
        quiet: bool = False,
        prefix: str = "",
        timeout: int = 10,
        namespace: Optional[Dict[str, str]] = None,
        start_stop: bool = False,
    ):
        self.path = path
        self.quiet = quiet
        self.prefix = prefix
        self.start_stop = start_stop
        self.namespace = NAMESPACE if namespace is None else namespace
        self.tolerant = tolerant
        self.timeout = timeout
        self.load_definitions()
        self.load_commands(modules=modules)

    def load_definitions(self) -> None:
        """
        To handle resolves pointing to objects not yet defined, we simply do
        two passes. Of course, it would be better to handle the dependency
        graph in one pass, but this is simpler and seems to be fast enough.
        """

        self.load_definitions_aux()
        self.load_definitions_aux()

    def load_definitions_aux(self) -> None:
        file_ = files.locate(
            self.path,
            "i-common-definitions.xml",
            flags=self.flags,
            shell=self.shell,
            timeout=self.timeout,
        )
        if not file_:
            raise OSError('unable to locate "i-common-definitions.xml"')
        try:
            with open(file_, encoding="utf-8") as x:
                root = self.parse(x)
            for child in root:
                if self.tag_is(child, "interfacefile"):
                    filename = child.attrib.get("filename")
                    if filename is not None:
                        self.load_definitions_aux_i(filename)
                else:
                    raise UnexpectedTagError(
                        'unexpected tag "{}"'.format(child.tag)
                    )
        except (OSError, ET.ParseError, UnicodeDecodeError) as e:
            msg = 'in file "{}", {} error: "{}"'.format(file_, type(e), e)
            if not self.tolerant:
                raise Exception(msg)
            elif not self.quiet:
                print(self.prefix + msg)

    def load_definitions_aux_i(self, filename: str) -> None:
        file_ = files.locate(
            self.path,
            filename,
            flags=self.flags,
            shell=self.shell,
            timeout=self.timeout,
        )
        if not file_:
            raise OSError('unable to locate "{}"'.format(filename))
        try:
            with open(file_, encoding="utf-8") as x:
                root = self.parse(x)
            for child in root:
                self.do_define(child)
        except (OSError, ET.ParseError, UnicodeDecodeError) as e:
            msg = 'in file "{}", {} error: "{}"'.format(file_, type(e), e)
            if not self.tolerant:
                raise Exception(msg)
            elif not self.quiet:
                print(self.prefix + msg)

    def load_commands(self, modules: bool = True) -> None:
        self.to_load = set()

        main = files.locate(
            self.path,
            "i-context.xml",
            flags=self.flags,
            shell=self.shell,
            timeout=self.timeout,
        )
        if main:
            dir_ = os.path.split(main)[0]
            for file_ in os.listdir(dir_):
                if self.load_commands_aux(file_):
                    self.to_load.add(os.path.join(dir_, file_))

        if modules:
            # Let's use `t-rst.xml` as a smoking gun.
            alt = files.locate(
                self.path,
                "t-rst.xml",
                flags=self.flags,
                shell=self.shell,
                timeout=self.timeout,
            )
            if alt:
                dir_ = os.path.split(alt)[0]
                for file_ in os.listdir(dir_):
                    if self.load_commands_aux(file_):
                        self.to_load.add(os.path.join(dir_, file_))

        self.load_commands_aux_i()

    def load_commands_aux(self, file_: str) -> bool:
        return (
            file_.endswith(".xml") and
            file_ != "context-en.xml" and
            not file_.startswith("i-common") and
            not file_.startswith("i-context")
        )

    def load_commands_aux_i(self) -> None:
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
                if not self.tolerant:
                    raise Exception(msg)
                elif not self.quiet:
                    print(self.prefix + msg)

    def do_define(self, node: ET.Element) -> None:
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

    def do_command(self, node: ET.Element) -> None:
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

    def do_command_aux(self, name: str, node: ET.Element) -> None:
        attrib = node.attrib

        if attrib.get("type") == "environment":
            begin = self.clean_name(attrib.get("begin", "start") + name)
            end = self.clean_name(attrib.get("end", "stop") + name)
            node_copy = copy.deepcopy(node)
            args = self.find(node_copy, "arguments")
            if self.start_stop:
                if args:
                    args.append(self.dots_node())
                    args.append(self.delim_node(end))
                else:
                    node_copy.append(self.tail_args_node(end))
            self.do_command_aux_i(begin, node_copy)
            # We could signal primitives in a better way. For now they are
            # implicitly signalled by setting file equal to `None`.
            self.do_command_aux_i(end, self.empty_node(attrib.get("file")))
        else:
            self.do_command_aux_i(self.clean_name(name), node)

    def do_command_aux_i(self, name: str, node: ET.Element) -> None:
        arguments = self.find(node, "arguments")
        handlers = {
            "angles": self.do_angles,
            "apply": self.do_apply,
            "assignments": self.do_assignments,
            "content": self.do_content,
            "csname": self.do_csname,
            "delimiter": self.do_delimiter,
            "index": self.do_index,
            "keywords": self.do_keywords,
            "position": self.do_position,
            "resolve": self.do_resolve,
            "string": self.do_string,
            "template": self.do_template,
            "text": self.do_text,
            "triplet": self.do_triplet,
            # This one is an addition of ours for convenience.
            "dotsdelimiter": self.do_dots_delimiter,
        }
        content = []
        for child in arguments:
            if self.tag_is(child, *handlers):
                content.append(handlers[self.raw_tag(child)](child))
            else:
                message = 'unexpected tag, name: "{}", attrib: "{}", tag: "{}"'
                tag, attrib = child.tag, child.attrib
                msg = message.format(name, attrib, tag)
                if self.tolerant:
                    content.append(
                        self.do_generic(tag.upper(), tag.lower(), attrib)
                    )
                    print(self.prefix + msg)
                else:
                    raise UnexpectedTagError(msg)
        self.add_cmd(
            name,
            {"con": self.flatten(content), "fil": node.attrib.get("file")},
        )

    def do_constant(self, node: ET.Element) -> str:
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

    def do_keywords(self, node: ET.Element) -> Dict[str, Any]:
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
            "con": content,
            "ren": self.render("keywords", node.attrib),
            "inh": inherits,
            "opt": self.is_true(node.attrib.get("optional")),
        }

    def do_assignments(self, node: ET.Element) -> Dict[str, Any]:
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
            "inh": inherits,
            "opt": self.is_true(node.attrib.get("optional")),
        }

    def do_parameter(self, node: ET.Element) -> List[Any]:
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
        return content

    def do_delimiter(self, node: ET.Element) -> Dict[str, Any]:
        return {
            "con": None,
            "inh": None,
            "opt": False,
            "ren": self.render("delimiter", node.attrib),
        }

    def do_dots_delimiter(self, node: ET.Element) -> Dict[str, Any]:
        return {"con": None, "inh": None, "opt": False, "ren": "..."}

    def do_angles(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("ANGLES", "angles", node.attrib)

    def do_template(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("TEMPLATE", "template", node.attrib)

    def do_apply(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("APPLY", "apply", node.attrib)

    def do_text(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("TEXT", "text", node.attrib)

    def do_string(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("STRING", "string", node.attrib)

    def do_index(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("INDEX", "index", node.attrib)

    def do_position(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("POSITION", "position", node.attrib)

    def do_triplet(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("TRIPLET", "triplet", node.attrib)

    def do_csname(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("CSNAME", "csname", node.attrib)

    def do_content(self, node: ET.Element) -> Dict[str, Any]:
        return self.do_generic("CONTENT", "content", node.attrib)

    def do_generic(
        self, type_: str, render: str, attrib: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "con": "<typ>{}</typ>".format(self.escape(type_)),
            "inh": None,
            "opt": self.is_true(attrib.get("optional")),
            "ren": self.render(render, attrib),
        }

    def do_resolve(self, node: ET.Element):
        name = node.attrib["name"]
        return self.defs.get(name)

    def do_inherit(self, node: ET.Element) -> str:
        return node.attrib["name"]

    def render(self, mode: str, attrib: Dict[str, Any]) -> str:
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
        elif mode in {"content", "text", "string"}:
            return "<pun>{</pun>...<pun>}</pun>"
        elif mode == "delimiter":
            return html_css.control_sequence(self.escape(attrib["name"]))
        else:
            msg = 'unexpected mode, mode: "{}", attrib: "{}"'
            if not self.tolerant:
                raise UnexpectedModeError(msg.format(mode, attrib))
            elif not self.quiet:
                print(self.prefix + msg.format(mode, attrib))
            return "..."

    def is_true(self, val: Any) -> bool:
        return val == "yes"

    def flatten(self, obj):
        if not obj:
            return None
        elif isinstance(obj, list):
            if len(obj) == 1:
                return self.flatten(obj[0])
            elif all(
                isinstance(x, str) or (
                    isinstance(x, list) and all(isinstance(y, str) for y in x)
                )
                for x in obj
            ):
                result = []
                for x in obj:
                    if isinstance(x, str):
                        result.append(x)
                    else:
                        result += x
                return result
            return [self.flatten(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: self.flatten(v) for k, v in obj.items()}
        return obj

    def transform(self, text: str, escape: bool = True) -> str:
        """
        This is the main place to add special formatting options. I think this
        degree of customization is a reasonable default, but there are lots of
        options here.
        """

        f = self.escape if escape else self.identity
        if text == "cd:sign":
            return f("[+-]")
        elif text.startswith("cd:"):
            rest = text[3:]
            if rest == "oneargument":
                return html_css.control_sequence("...") + "<par>#1</par>"
            elif rest == "twoarguments":
                return html_css.control_sequence("...") + "<par>#1#2</par>"
            elif rest == "threearguments":
                return html_css.control_sequence("...") + "<par>#1#2#3</par>"
            elif rest in {"command", "content", "text", "string"}:
                return "<pun>{</pun>...<pun>}</pun>"
            # These go too far?
            # elif rest == "template":
            #     return "<pun>|</pun>...<pun>|</pun>"
            # elif rest == "number":
            #     return "<num>NUMBER</num>"
            # elif rest == "dimension":
            #     return "<wor>DIMENSION</wor>"
            return "<typ>" + f(rest.upper()) + "</typ>"
        return f(text)

    def escape(self, text: str) -> str:
        return html.escape(text, quote=False)

    def identity(self, text: str) -> str:
        return text

    def clean_name(self, text: str) -> str:
        return text.replace("​", "")  # remove zero-width whitespace

    def empty_node(self, file_: Optional[str]) -> ET.Element:
        return ET.fromstring((
            '<cd:command xmlns:cd="http://www.pragma-ade.com/commands" '
            'file="{}" />'
        ).format(file_))

    def dots_node(self) -> ET.Element:
        return ET.fromstring(
            '<cd:dotsdelimiter xmlns:cd="http://www.pragma-ade.com'
            '/commands" />'
        )

    def delim_node(self, name: str) -> ET.Element:
        return ET.fromstring((
            '<cd:delimiter xmlns:cd="http://www.pragma-ade.com/commands" '
            'name="{}" />'
        ).format(name))

    def tail_args_node(self, name: str) -> ET.Element:
        return ET.fromstring((
            '<cd:arguments xmlns:cd="http://www.pragma-ade.com/commands">'
            '<cd:dotsdelimiter xmlns:cd="http://www.pragma-ade.com/commands" '
            '/>'
            '<cd:delimiter xmlns:cd="http://www.pragma-ade.com/commands" '
            'name="{}" />'
            '</cd:arguments>'
        ).format(name))

    def find(self, node: ET.Element, query: str) -> Iterable:
        result = node.find(self.get_tag(query))
        return result if result else []

    def findall(self, node: ET.Element, query: str) -> Iterable:
        result = node.findall(self.get_tag(query))
        return result if result else []

    def tag_is(self, node: ET.Element, *tags: str) -> bool:
        return node.tag in [self.get_tag(tag) for tag in tags]

    def get_tag(self, tag: str) -> str:
        return "{%s}%s" % (self.namespace.get("cd"), tag)

    def raw_tag(self, node: ET.Element) -> str:
        return node.tag.rsplit("}", maxsplit=1)[-1]

    def add_def(self, name: str, obj) -> None:
        self.defs[name] = obj

    def get_def(self, name: str):
        if name in self.defs:
            return self.defs[name]
        for key, val in UGLY_DEF_LOOKUP.items():
            if name == key:
                return self.get_def(val)
        message = "unexpected resolve, could not find '{}'"
        raise DefinitionNotFoundError(message.format(name))

    def add_cmd(self, name: str, obj) -> None:
        if name in self.cmds:
            self.cmds[name].append(obj)
        else:
            self.cmds[name] = [obj]

    # This needs re-doing.
    def simplify(self) -> None:
        for name in self.cmds:
            self.cmds[name] = self.simplify_aux(self.cmds[name])

    def simplify_aux(self, vars_: T) -> T:
        if isinstance(vars_, list):
            return utilities.deduplicate_list(vars_)
        return vars_

    def encode(self):
        self.simplify()
        return self.cmds
