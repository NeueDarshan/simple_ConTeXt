# this script handles XML files describing the ConTeXt interface, and can
# output a JSON file describing all the commands
import xml.etree.ElementTree as ET
import collections
import itertools
import copy
import json


NAMESPACES = {
    "cd": "http://www.pragma-ade.com/commands",
}

JOIN_STYLES = {
    "range": ":",
    "factor": "*",
    "apply": "->",
    "none": "",
}

DELIMITERS = {
    "braces": ["{", "}"],
    "parentheses": ["(", ")"],
    "default": ["[", "]"],
    "none": ["", ""],
}


def _tag_is(element, tag):
    return element.tag == "{%s}%s" % (NAMESPACES["cd"], tag)


def _translate_name(string):
    if string == "cd:sign":
        return "[+-]"
    elif string.startswith("cd:"):
        return string[3:].upper()
    else:
        return string


def _translate_constant(element):
    join = JOIN_STYLES[element.get("method", "none")]
    prefix = _translate_name(element.get("prefix", ""))
    type_ = _translate_name(element.get("type"))

    content = prefix + join + type_
    if element.get("default") == "yes":
        return {"content": content, "default": True}
    else:
        return content


def _iter_power_set(iterable):
    list_ = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(list_, n) for n in range(len(list_) + 1))


def handle_sub_element(element, definitions):
    if _tag_is(element, "constant"):
        return _translate_constant(element)

    elif _tag_is(element, "inherit"):
        return "inherits: \\{name}".format(**element.attrib)

    elif _tag_is(element, "resolve"):
        possible_references = [
            def_ for def_ in definitions
            if element.get("name") == def_.get("name")]
        def_ = possible_references.pop()
        def_.tag = "{%s}keywords" % NAMESPACES["cd"]
        return handle_syntax_element(def_, definitions)["description"]

    else:
        raise Exception(
            "unknown tag '{}' in keywords list".format(element.tag))


def handle_keywords(element, definitions):
    middle = "...,..." if element.get("list") == "yes" else "..."
    delims = DELIMITERS[element.get("delimiters", "default")]

    description = []
    for child in element:
        sub_element = handle_sub_element(child, definitions)
        if isinstance(sub_element, list):
            description += sub_element
        else:
            description.append(sub_element)

    return {
        "description": description,
        "inherits": None,
        "optional": element.get("optional") == "yes",
        "rendering": delims[0] + middle + delims[1],
    }


def handle_assignments(element, definitions):
    middle = "..,..=..,.." if element.get("list") == "yes" else "..=.."
    delims = DELIMITERS[element.get("delimiters", "default")]

    description = collections.OrderedDict()
    inherits = None
    for i, child in enumerate(element):
        if _tag_is(child, "parameter"):
            list_ = []
            for parameter in child:
                sub_element = handle_sub_element(parameter, definitions)
                if isinstance(sub_element, list):
                    list_ += sub_element
                else:
                    list_.append(sub_element)
            description[_translate_name(child.get("name"))] = list_
        elif _tag_is(child, "inherit"):
            inherits = child.get("name")
        else:
            message = "unexpected child tag '{}' in element '{}'"
            raise Exception(message.format(child.tag, element))

    return {
        "description": description,
        "inherits": inherits,
        "optional": element.get("optional") == "yes",
        "rendering": delims[0] + middle + delims[1],
    }


def handle_delimiter(element):
    name = element.get("name")
    rendering = ("\\" if name.isalpha() else "") + name
    return {
        "description": None,
        "inherits": None,
        "optional": element.get("optional") == "yes",
        "rendering": rendering,
    }


def handle_resolve(element, definitions):
    try:
        possible_references = [
            definition for definition in definitions
            if element.get("name") == definition.get("name")]
        definition = possible_references.pop()
        return handle_syntax_element(definition[0], definitions)

    except IndexError as e:
        message = "can't resolve argument '{}'".format(element.get("name"))
        raise Exception(message)


def define_generic_handler(description, rendering):
    return lambda element: {
        "description": description,
        "inherits": None,
        "optional": element.get("optional") == "yes",
        "rendering": rendering,
    }


def handle_syntax_element(element, definitions):
    handlers = {
        "keywords": lambda e: handle_keywords(e, definitions),
        "assignments": lambda e: handle_assignments(e, definitions),
        "content": define_generic_handler("CONTENT", "{...}"),
        "csname": define_generic_handler("CSNAME", "\\..."),
        "text": define_generic_handler("TEXT", "..."),
        "angles": define_generic_handler("CONTENT", "<<...>>"),
        "template": define_generic_handler("TEMPLATE", "[|...|]"),
        "triplet": define_generic_handler("TRIPLET", "[x:y:z,..]"),
        "position": define_generic_handler("POSITION", "(...,...)"),
        "index": define_generic_handler("INDEX", "[..+...+..]"),
        "apply": define_generic_handler("APPLY", "[..,..=>..,..]"),
        "resolve": lambda e: handle_resolve(e, definitions),
        "delimiter": handle_delimiter,
    }
    for tag, handler in handlers.items():
        if _tag_is(element, tag):
            return handler(element)
    raise Exception("unknown argument type '{}'".format(element.tag))


def fix_tree(root):
    query = './/cd:interface//cd:command//cd:arguments//' \
        + 'cd:resolve[@name="keyword-name-optional-list"]'
    problem_commands = root.findall(query, namespaces=NAMESPACES)
    for command in problem_commands:
        command.set("name", "keyword-name-list-optional")

    xml = root.find(
        './/cd:interface[@file="i-xml.xml"]', namespaces=NAMESPACES)
    for child in xml:
        child.set("file", "lxml-ini.mkiv")

    new_arguments = [
        """<cd:define
        xmlns:cd="http://www.pragma-ade.com/commands"
        name="argument-content">
            <cd:keywords delimiters="braces">
                <cd:constant type="cd:content"/>
            </cd:keywords>
        </cd:define>""",

        """<cd:define
        xmlns:cd="http://www.pragma-ade.com/commands"
        name="argument-content-optional">
            <cd:keywords delimiters="braces" optional="yes">
                <cd:constant type="cd:content"/>
            </cd:keywords>
        </cd:define>""",

        """<cd:define
        xmlns:cd="http://www.pragma-ade.com/commands"
        name="argument-content-list">
            <cd:keywords delimiters="braces" list="yes">
                <cd:constant type="cd:content"/>
            </cd:keywords>
        </cd:define>""",

        """<cd:define
        xmlns:cd="http://www.pragma-ade.com/commands"
        name="argument-content-list-optional">
            <cd:keywords delimiters="braces" list="yes" optional="yes">
                <cd:constant type="cd:content"/>
            </cd:keywords>
        </cd:define>""",
    ]

    query = './/cd:interface[@file="i-common-definitions.xml"]' \
        + '//cd:interface[@file="i-common-argument.xml"]'
    common_arguments = root.find(query, namespaces=NAMESPACES)
    for arg in new_arguments:
        common_arguments.append(ET.fromstring(arg))


def parse_command_instance(element, definitions):
    command = {
        "name": None,
        "syntax": [],
        "file": element.get("file"),
    }

    arguments = element.find(".//cd:arguments", namespaces=NAMESPACES)
    if arguments:
        for argument in arguments:
            command["syntax"].append(
                handle_syntax_element(argument, definitions))

    if element.get("type") == "environment":
        command["name"] = element.get("begin", "start") + element.get("name")
        close_name = element.get("end", "stop") + element.get("name")
        command["syntax"] += [
            {
                "description": None,
                "inherits": None,
                "optional": False,
                "rendering": "...",
            },
            {
                "description": None,
                "inherits": None,
                "optional": False,
                "rendering": "\\" + close_name,
            }
        ]
        close_command = {
            "file": element.get("file"),
            "name": close_name,
            "syntax": [],
        }
        return [command, close_command]

    else:
        command["name"] = "{name}".format(**element.attrib)
        return [command]


def parse_context_tree(xml, pre_process=None):
    tree = ET.parse(xml)
    root = tree.getroot()
    if pre_process:
        pre_process(root)

    definition_list = [
        child for child in root.iterfind(
            ".//cd:interface//cd:define", namespaces=NAMESPACES)]
    command_list = [
        child for child in root.iterfind(
            ".//cd:interface//cd:command", namespaces=NAMESPACES)]

    command_dict = {}
    for command in command_list:
        try:
            instances = parse_command_instance(command, definition_list)
        except Exception as e:
            print('While parsing command "{}" got error "{}"'.format(
                command.get("name"), e))
        for command_instance in instances:
            name = command_instance["name"]
            new_command_syntax = command_instance["syntax"]

            if name not in command_dict:
                command_dict[name] = {
                    "syntax_variants": [new_command_syntax],
                    "files": [command_instance["file"]],
                }

            elif not any(
                new_command_syntax == previous_command_syntax
                    for previous_command_syntax
                    in command_dict[name]["syntax_variants"]
            ):
                command_dict[name]["syntax_variants"].append(
                    new_command_syntax)
                if command_instance["file"] not in command_dict[name]["files"]:
                    command_dict[name]["files"].append(
                        command_instance["file"])

    return command_dict


def rendered_command_dict(commands):
    rendered_commands = {}

    def _translate_keyword(object_):
        if isinstance(object_, str):
            return object_
        elif isinstance(object_, dict):
            if object_.get("default"):
                return "<u>{}</u>".format(object_["content"])
            else:
                return object_["content"]
        else:
            raise Exception(
                "unexpected entry of type '{}'".format(type(object_)))

    def _process_str(description, n, lines):
        lines.append("{:<2}  {}".format(n, description))

    def _process_list(description, n, lines):
        if len(description) == 0:
            return
        lines.append("{:<2}  {}".format(
            n, " ".join(_translate_keyword(item) for item in description)
        ))

    def _process_dict(description, n, lines):
        if len(description) == 0:
            return

        template = "{:<%s} = {}" % max(len(cmd) for cmd in description)
        assignments = []
        for key, value in description.items():
            if isinstance(value, str):
                assignments.append(template.format(key, value))
            elif isinstance(value, list):
                assignments.append(template.format(
                    key, " ".join(_translate_keyword(e) for e in value)))
            elif isinstance(value, dict):
                assignments.append(template.format(
                    key, _translate_keyword(value)))
            else:
                message = "unexpected entry of type '{}' in argument '{}'"
                raise Exception(message.format(type(value), key))

        for i, assignment in enumerate(assignments):
            if i == 0:
                lines.append("{:<2}  {}".format(n, assignment))
            else:
                lines.append("    {}".format(assignment))

    def _inherit_str(inherits, n, lines):
        if len(lines) > 0:
            lines.append("    inherits: \\{}".format(inherits))
        else:
            lines.append("{:<2}  inherits: \\{}".format(n, inherits))

    def _inherit_list(inherits, n, lines):
        for inheritance in inherits:
            if len(lines) > 0:
                lines.append("    inherits: \\{}".format(inheritance))
            else:
                lines.append("{:<2}  inherits: \\{}".format(n, inheritance))

    for name, info in commands.items():
        rendered_commands[name] = []

        try:
            for syntax_variant in info["syntax_variants"]:
                full_rendering = [None] * 3
                full_rendering[1] = "\\" + name
                full_rendering[0] = " " * len(full_rendering[1])
                full_rendering[2] = " " * len(full_rendering[1])

                doc_string = []
                if syntax_variant:
                    n = 1
                    for variant in syntax_variant:
                        description = variant["description"]
                        inherits = variant["inherits"]
                        rendering = variant["rendering"]
                        length = len(rendering)

                        if (description is None) and (inherits is None):
                            full_rendering[0] += " " * (length+1)
                            full_rendering[1] += " " + rendering
                            full_rendering[2] += " " * (length+1)

                        else:
                            lines = []
                            full_rendering[1] += " " + rendering
                            if length > 3:
                                str_ = "  {:^%s}" % (length-1)
                                full_rendering[0] += str_.format(n)
                                full_rendering[2] += str_.format(
                                    "OPT" if variant["optional"] else "")
                            else:
                                str_ = " {:^%s}" % length
                                full_rendering[0] += str_.format(n)
                                full_rendering[2] += str_.format(
                                    "OPT" if variant["optional"] else "")

                            if isinstance(description, str):
                                _process_str(description, n, lines)
                            elif isinstance(description, list):
                                _process_list(description, n, lines)
                            elif isinstance(description, dict):
                                _process_dict(description, n, lines)
                            else:
                                str_ = "unexpected argument of type '{}'"
                                raise Exception(str_.format(type(description)))

                            if isinstance(inherits, str):
                                _inherit_str(inherits, n, lines)
                            elif isinstance(inherits, list):
                                _inherit_list(inherits, n, lines)
                            elif inherits is None:
                                pass
                            else:
                                str_ = "unexpected inheritance of type '{}'"
                                raise Exception(str_.format(type(inherits)))

                            doc_string.append(lines)
                            n += 1

                for i in range(2, -1, -1):
                    full_rendering[i] = full_rendering[i].rstrip()
                    if len(full_rendering[i]) == 0:
                        del full_rendering[i]

                rendered_commands[name].append([
                    "\n".join(full_rendering),
                    "\n\n".join("\n".join(lines) for lines in doc_string)
                ])

            rendered_commands[name].append(info["files"])

        except Exception as e:
            message = "error '{}' occurred whilst processing command '{}'"
            raise Exception(message.format(repr(e), name))

    for name, entry in rendered_commands.items():
        rendered_commands[name] = sorted(entry[:-1]) + [entry[-1]]

    return rendered_commands


def simplified_syntax_variants(variants):
    length = len(variants)
    if length <= 1:
        return variants

    variants_copy = copy.deepcopy(variants)

    def _iter_without_optional_syntax_variants(syntax):
        length = len(syntax)
        optional_syntax_indices = [
            i for i in range(length) if syntax[i]["optional"]]
        mandatory_syntax_indices = [
            i for i in range(length) if i not in optional_syntax_indices]
        for combination in _iter_power_set(optional_syntax_indices):
            indices = set(combination)
            indices.update(mandatory_syntax_indices)
            yield [syntax[i] for i in sorted(indices)]

    def _iter_changing_mandatory_to_optional_syntax_variants(syntax):
        mandatory_syntax_indices = [
            i for i in range(len(syntax)) if not syntax[i]["optional"]]
        copy_ = copy.deepcopy(syntax)
        for combination in _iter_power_set(mandatory_syntax_indices):
            for i in mandatory_syntax_indices:
                copy_[i]["optional"] = True if i in combination else False
            yield copy_

    def _is_copy_without_optional_syntax(other, master):
        for _reduced_syntax_variant in \
                _iter_without_optional_syntax_variants(master):
            if _reduced_syntax_variant == other:
                return True
        return False

    done = False
    while not done:
        done = True
        ordered_pairs = list(itertools.permutations(
            [(n, entry) for n, entry in enumerate(variants_copy)], 2))
        for pair in ordered_pairs:
            i, master = pair[0]
            j, other = pair[1]
            found_redundancy = False
            for master_variant in \
                    _iter_changing_mandatory_to_optional_syntax_variants(
                        master):
                if _is_copy_without_optional_syntax(other, master_variant):
                    variants_copy[i] = master_variant
                    del variants_copy[j]
                    found_redundancy = True
                    break
            if found_redundancy:
                done = False
                break

    return variants_copy


def simplify_commands(commands):
    for name, command in commands.items():
        command["syntax_variants"] = simplified_syntax_variants(
            command["syntax_variants"])
