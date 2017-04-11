# this script handles XML files describing the ConTeXt interface, and can
# output a JSON file describing all the commands
import xml.etree.ElementTree as ET
import collections
import itertools
import copy


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
    query = './cd:command//cd:resolve[@name="keyword-name-optional-list"]'
    problems = root.findall(query, namespaces=NAMESPACES)
    for command in problems:
        command.set("name", "keyword-name-list-optional")

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
    for arg in new_arguments:
        root.append(ET.fromstring(arg))


def parse_command_instance(element, definitions):
    command = {
        "name": None,
        "syntax": [],
        "file": element.get("file"),
    }

    arguments = element.find("./cd:arguments", namespaces=NAMESPACES)
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


def parse_context_tree(xml):
    def_list = [
        child for child in xml.getroot().iterfind(
            "./cd:define", namespaces=NAMESPACES)]
    command_list = [
        child for child in xml.getroot().iterfind(
            "./cd:command", namespaces=NAMESPACES)]

    commands = {}
    for command in command_list:
        try:
            instances = parse_command_instance(command, def_list)
            for instance in instances:
                name = instance["name"]
                syntax = instance["syntax"]

                if name not in commands:
                    commands[name] = {
                        "syntax_variants": [syntax],
                        "files": [instance["file"]],
                    }

                elif not any(
                    syntax == prev_syntax
                    for prev_syntax in commands[name]["syntax_variants"]
                ):
                    commands[name]["syntax_variants"].append(syntax)
                    if instance["file"] not in commands[name]["files"]:
                        commands[name]["files"].append(instance["file"])

        except Exception as e:
            message = 'While parsing command "{}" got error "{}"'
            print(message.format(command.get("name"), e))

    return commands


def _translate_keyword(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        if obj.get("default"):
            return "<u>{}</u>".format(obj["content"])
        else:
            return obj["content"]
    else:
        message = "unexpected entry of type '{}'"
        raise Exception(message.format(type(obj)))


def _process_str(desc, n, lines):
    lines.append("{:<2}  {}".format(n, desc))


def _process_list(desc, n, lines):
    if len(desc) > 0:
        str_ = " ".join(_translate_keyword(item) for item in desc)
        lines.append("{:<2}  {}".format(n, str_))


def _process_dict(desc, n, lines):
    if len(desc) == 0:
        return

    template = "{:<%s} = {}" % max(len(cmd) for cmd in desc)
    assignments = []
    for key, val in desc.items():
        if isinstance(val, str):
            assignments.append(template.format(key, val))
        elif isinstance(val, list):
            assignments.append(template.format(
                key, " ".join(_translate_keyword(e) for e in val)))
        elif isinstance(val, dict):
            assignments.append(template.format(
                key, _translate_keyword(val)))
        else:
            message = "unexpected entry of type '{}' in argument '{}'"
            raise Exception(message.format(type(val), key))

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


def rendered_command(name, dict_):
    result = []
    for syntax in dict_["syntax_variants"]:
        str_ = [None] * 3
        str_[1] = "\\" + name
        str_[0] = " " * len(str_[1])
        str_[2] = " " * len(str_[1])

        doc_string = []
        if syntax:
            n = 1
            for var in syntax:
                desc = var["description"]
                inherits = var["inherits"]
                string = var["rendering"]
                len_ = len(string)

                if (desc is None) and (inherits is None):
                    str_[0] += " " * (len_+1)
                    str_[1] += " " + string
                    str_[2] += " " * (len_+1)

                else:
                    lines = []
                    str_[1] += " " + string
                    if len_ > 3:
                        temp = "  {:^%s}" % (len_-1)
                        str_[0] += temp.format(n)
                        str_[2] += temp.format(
                            "OPT" if var["optional"] else "")
                    else:
                        temp = " {:^%s}" % len_
                        str_[0] += temp.format(n)
                        str_[2] += temp.format(
                            "OPT" if var["optional"] else "")

                    if isinstance(desc, str):
                        _process_str(desc, n, lines)
                    elif isinstance(desc, list):
                        _process_list(desc, n, lines)
                    elif isinstance(desc, dict):
                        _process_dict(desc, n, lines)
                    else:
                        msg = "unexpected argument of type '{}'"
                        raise Exception(msg.format(type(desc)))

                    if inherits is None:
                        pass
                    elif isinstance(inherits, str):
                        _inherit_str(inherits, n, lines)
                    elif isinstance(inherits, list):
                        _inherit_list(inherits, n, lines)
                    else:
                        msg = "unexpected inheritance of type '{}'"
                        raise Exception(msg.format(type(inherits)))

                    doc_string.append(lines)
                    n += 1

        for i in range(2, -1, -1):
            str_[i] = str_[i].rstrip()
            if len(str_[i]) == 0:
                del str_[i]

        result.append([
            "\n".join(str_),
            "\n\n".join("\n".join(lines) for lines in doc_string)
        ])

    return sorted(result), dict_["files"]


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
