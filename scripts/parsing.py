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

# miscellaneous helper functions
def _tag_is(element, tag):
    return element.tag == "{{{cd}}}{tag}".format(cd=NAMESPACES["cd"], tag=tag)

def _translate_name(string):
    if string == "cd:sign":
        new_string = "[+-]"
    elif string.startswith("cd:"):
        new_string = string[3:].upper()
    else:
        new_string = string
    return new_string

def _translate_constant(element):
    join = JOIN_STYLES[element.get("method", "none")]

    prefix = _translate_name(element.get("prefix", ""))
    type_ = _translate_name(element.get("type"))

    content = "{prefix}{join}{type}".format(
        prefix=prefix, join=join, type=type_)

    # we 'usually' return a dict of the form {"content": "foo",
    # "default": True/False}, but consider "foo" as an acceptable shorthand for
    # {"content": "foo", "default": False}.
    if element.get("default") == "yes":
        return {"content": content, "default": True}
    else:
        return content

def _iter_power_set(iterable):
    list_ = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(list_, n) for n in range(len(list_)+1))

# these couple functions process bits and pieces within a cd:command node
def handle_sub_element(element, definitions):
    if _tag_is(element, "constant"):
        return _translate_constant(element)

    elif _tag_is(element, "inherit"):
        return "inherits: \\{name}".format(**element.attrib)

    elif _tag_is(element, "resolve"):
        possible_references = [
            definition for definition in definitions
            if element.get("name") == definition.get("name")]

        def_ = possible_references[0]
        def_.tag = "{{{cd}}}keywords".format(**NAMESPACES)
        return handle_syntax_element(def_, definitions)["description"]

    else:
        raise Exception(
            "unknown tag '{tag}' in keywords list".format(tag=element.tag))

def handle_keywords(element, definitions):
    if element.get("list") == "yes":
        middle = "...,..."
    else:
        middle = "..."
    delims = DELIMITERS[element.get("delimiters", "default")]

    description = []
    for child in element:
        sub_element = handle_sub_element(child, definitions)
        if isinstance(sub_element, list):
            description += sub_element
        else:
            description.append(sub_element)

    return {
        "rendering": delims[0] + middle + delims[1],
        "description": description,
        "inherits": None,
        "optional": element.get("optional") == "yes",
    }

def handle_assignments(element, definitions):
    if element.get("list") == "yes":
        middle = "..,..=..,.."
    else:
        middle = "..=.."
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
            raise Exception("unexpected child tag {tag} in element {e}".format(
                tag=child.tag, e=element))

    return {
        "rendering": delims[0] + middle + delims[1],
        "description": description,
        "inherits": inherits,
        "optional": element.get("optional") == "yes",
    }

def handle_delimiter(element):
    name = element.get("name")
    if name.isalpha():
        rendering = "\\{name}".format(name=name)
    else:
        rendering = "{name}".format(name=name)

    return {
        "rendering": rendering,
        "description": None,
        "inherits": None,
        "optional": element.get("optional") == "yes",
    }

def handle_resolve(element, definitions):
    try:
        possible_references = [
            definition for definition in definitions
            if element.get("name") == definition.get("name")]

        return handle_syntax_element(possible_references[0][0], definitions)

    except IndexError as e:
        raise Exception("can't resolve argument '{name}'".format(
            name=element.get("name")))

def define_generic_handler(description, rendering):
    def handle_generic(element):
        return {
            "rendering": rendering,
            "description": description,
            "inherits": None,
            # I'd be surprised to learn there are any optional delimiters...
            # but we can handle them like this at no extra cost
            "optional": element.get("optional") == "yes",
        }
    return handle_generic

# just a wrapper around the previous handlers
def handle_syntax_element(element, definitions):
    handlers = {
        # various sorts of argument
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
        # delimiters can be mixed in-between 'actual' arguments
        "delimiter": handle_delimiter,
    }

    if not any(_tag_is(element, tag) for tag in handlers):
        raise Exception("unknown argument type '{tag}'".format(
            tag=element.tag))

    for tag, handler in handlers.items():
        if _tag_is(element, tag):
            return handler(element)

# these fixes apply to the TeXLive 2016 (combined) interface XML file
def fix_context_tree(root_node):
    # fix \setupitemgroup, resolve->inherit
    itemgroup = root_node.find(
        './/cd:interface[@file="i-itemgroup.xml"]', namespaces=NAMESPACES)
    setupitemgroup = itemgroup.findall(
        './/cd:command[@name="setupitemgroup"]', namespaces=NAMESPACES)
    for variant in setupitemgroup:
        query = './/cd:arguments//cd:assignments' \
            + '//cd:parameter[@name="indenting"]//cd:resolve'
        problem = variant.find(query, namespaces=NAMESPACES)
        problem.tag = "{{{cd}}}inherit".format(**NAMESPACES)

    # fix \definefontfamilypreset, assignment->assignments
    fontfamily = root_node.find(
        './/cd:interface[@file="i-fontfamily.xml"]', namespaces=NAMESPACES)
    definefontfamilypreset = fontfamily.iterfind(
        './/cd:command[@name="definefontfamilypreset"]', namespaces=NAMESPACES)
    for variant in definefontfamilypreset:
        query = './/cd:arguments//cd:assignment'
        problem = variant.find(query, namespaces=NAMESPACES)
        if problem:
            problem.tag = "{{{cd}}}assignments".format(**NAMESPACES)

    # fix \setupfittingpage, defaut->default
    fittingpage = root_node.find(
        './/cd:interface[@file="i-fittingpage.xml"]', namespaces=NAMESPACES)
    setupfittingpage = fittingpage.find(
        './/cd:command[@name="setupfittingpage"]', namespaces=NAMESPACES)
    query = './/cd:arguments//cd:assignments//cd:parameter[@name="paper"]' \
        + '//cd:constant[@type="defaut"]'
    problem = setupfittingpage.find(query, namespaces=NAMESPACES)
    problem.set("type", "default")

    # fix \currentdate, moth->month
    conversion = root_node.find(
        './/cd:interface[@file="i-conversion.xml"]', namespaces=NAMESPACES)
    currentdate = conversion.find(
        './/cd:command[@name="currentdate"]', namespaces=NAMESPACES)
    query = './/cd:arguments//cd:keywords//cd:constant[@type="moth"]'
    problem = currentdate.find(query, namespaces=NAMESPACES)
    problem.set("type", "month")

    # fix \defineenumerations, defineenumerations->defineenumeration
    enumeration = root_node.find(
        './/cd:interface[@file="i-enumeration.xml"]', namespaces=NAMESPACES)
    defineenumerations = enumeration.find(
        './/cd:command[@name="defineenumerations"]', namespaces=NAMESPACES)
    defineenumerations.set("name", "defineenumeration")

    # fix: keyword-name-optional-list->keyword-name-list-optional
    query = './/cd:interface//cd:command//cd:arguments//' \
        + 'cd:resolve[@name="keyword-name-optional-list"]'
    problem_commands = root_node.findall(query, namespaces=NAMESPACES)
    for command in problem_commands:
        command.set("name", "keyword-name-list-optional")

    # fix: we don't understand a file attribute in the interface element in the
    # main parsers, we only understand it on the command element itself. As
    # such, we tweak the XML to obey this convention.
    xml = root_node.find(
        './/cd:interface[@file="i-xml.xml"]', namespaces=NAMESPACES)
    for child in xml:
        child.set("file", "lxml-ini.mkiv")

    # add the new common argument types:
    #   + argument-content
    #   + argument-content-optional
    #   + argument-content-list
    #   + argument-content-list-optional
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
        </cd:define>"""]

    query = './/cd:interface[@file="i-common-definitions.xml"]' \
        + '//cd:interface[@file="i-common-argument.xml"]'
    common_arguments = root_node.find(query, namespaces=NAMESPACES)
    for arg in new_arguments:
        common_arguments.append(ET.fromstring(arg))

# high-level function, fully processes one cd:command node;
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
        command["name"] = "{begin}{name}".format(
            begin=element.get("begin", "start"),
            name=element.get("name"))

        close_name = "{end}{name}".format(
            end=element.get("end", "stop"),
            name=element.get("name"))

        command["syntax"] += [
            {
                "rendering": "...",
                "description": None,
                "inherits": None,
                "optional": False,
            },
            {
                "rendering": "\\{end_name}".format(end_name=close_name),
                "description": None,
                "inherits": None,
                "optional": False,
            }
        ]

        close_command = {
            "name": close_name,
            "syntax": [],
            "file": element.get("file"),
        }

        return [command, close_command]

    else:
        command["name"] = "{name}".format(**element.attrib)

        return [command]

# a wrapper around parse_command_instance, which takes into account the fact
# that a single command can have multiple cd:command nodes describing it (if it
# has multiple different usages)
def parse_context_tree(context_xml, pre_process=None):
    tree = ET.parse(context_xml)
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
        for command_instance in parse_command_instance(
                command, definition_list):

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

# takes the result of parse_context_tree, which still retains a lot of
# structure from the original XML definitions, and turns it into a list of
# string descriptions of the commands (mimicking the style of e.g.
# setup-en.pdf)
def rendered_command_dict(commands):
    rendered_commands = {}

    def _translate_keyword(object_):
        if isinstance(object_, str):
            return object_
        elif isinstance(object_, dict):
            if object_.get("default"):
                # we use underlining in the JSON to indicate default arguments
                return "<u>{item}</u>".format(item=object_["content"])
            else:
                return object_["content"]
        else:
            raise Exception("unexpected entry of type {type}".format(
                type=type(object_)))

    def _process_str(description, n, lines):
        lines.append("{n:<2}  {desc}".format(n=n, desc=description))

    def _process_list(description, n, lines):
        if len(description) == 0:
            return

        lines.append("{n:<2}  {desc}".format(
            n=n,
            desc=" ".join(_translate_keyword(item) for item in description)
        ))

    def _process_dict(description, n, lines):
        if len(description) == 0:
            return

        max_command_len = max(len(cmd) for cmd in description)
        template = "{{key:<{len}}} = {{value}}".format(len=max_command_len)

        assignments = []
        for key, value in description.items():
            if isinstance(value, str):
                assignments.append(template.format(key=key, value=value))
            elif isinstance(value, list):
                assignments.append(template.format(
                    key=key,
                    value=" ".join(_translate_keyword(e) for e in value)))
            elif isinstance(value, dict):
                assignments.append(template.format(
                    key=key, value=_translate_keyword(value)))
            else:
                raise Exception(
                    "unexpected entry of type {type} in argument {arg}".format(
                        type=type(value), arg=key))

        for i, assignment in enumerate(assignments):
            if i == 0:
                lines.append("{n:<2}  {value}".format(n=n, value=assignment))
            else:
                lines.append("    {value}".format(value=assignment))

    def _inherit_str(inherits, n, lines):
        if len(lines) > 0:
            lines.append("    inherits: \\{name}".format(name=inherits))
        else:
            lines.append("{n:<2}  inherits: \\{name}".format(
                n=n, name=inherits))

    def _inherit_list(inherits, n, lines):
        for inheritance in inherits:
            if len(lines) > 0:
                lines.append("    inherits: \\{name}".format(name=inheritance))
            else:
                lines.append("{n:<2}  inherits: \\{name}".format(
                    n=n, name=inheritance))

    for name, info in commands.items():
        rendered_commands[name] = []

        try:
            for syntax_variant in info["syntax_variants"]:
                full_rendering = [None] * 3
                full_rendering[1] = "\\{name}".format(name=name)
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
                                full_rendering[0] += "  {{n:^{len}}}".format(
                                    len=length-1).format(n=n)
                                full_rendering[2] += "  {{s:^{len}}}".format(
                                    len=length-1).format(
                                        s="OPT" if variant["optional"] else "")
                            else:
                                full_rendering[0] += " {{n:^{len}}}".format(
                                    len=length).format(n=n)
                                full_rendering[2] += " {{s:^{len}}}".format(
                                    len=length).format(
                                        s="OPT" if variant["optional"] else "")

                            if isinstance(description, str):
                                _process_str(description, n, lines)

                            elif isinstance(description, list):
                                _process_list(description, n, lines)

                            elif isinstance(description, dict):
                                _process_dict(description, n, lines)

                            else:
                                raise Exception(
                                    "unexpected argument of type"
                                    " {type}".format(
                                        type=type(description), name=name))

                            if isinstance(inherits, str):
                                _inherit_str(inherits, n, lines)

                            elif isinstance(inherits, list):
                                _inherit_list(inherits, n, lines)

                            elif inherits is None:
                                pass

                            else:
                                raise Exception(
                                    "unexpected inheritance of type"
                                    " {type}".format(
                                        type=type(inherits)))

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
            raise Exception(
                "error '{e}' occurred whilst processing command {name}".format(
                    e=repr(e), name=name))

    for name, entry in rendered_commands.items():
        rendered_commands[name] = sorted(entry[:-1]) + [entry[-1]]

    return rendered_commands

# mulls over the multiple different syntaxes for each command, and where
# possible eliminates the redundant ones
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
                if i in combination:
                    copy_[i]["optional"] = True
                else:
                    copy_[i]["optional"] = False
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
        ordered_pairs = list(
            itertools.permutations(
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

def main():
    structured_commands = parse_context_tree(
        "context-en.xml", pre_process=fix_context_tree)

    simplify_commands(structured_commands)

    # structured_commands is the intermediate form we store the commands in; to
    # take a look at it you can do something like this to write it to file, but
    # be warned it is a very big (~100,000 lines long) file.
    # with open("pre_commands.json", mode="w") as f:
    #     json.dump(structured_commands, f, sort_keys=True, indent=2)

    flat_commands = rendered_command_dict(structured_commands)

    with open("commands.json", mode="w") as f:
        json.dump(flat_commands, f, sort_keys=True, indent=2)

if __name__ == "__main__":
    main()
