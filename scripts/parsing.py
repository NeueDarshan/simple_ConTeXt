import xml.etree.ElementTree as ET
import collections
import itertools
import string
import copy
import os


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
    "braces": "{}",
    "parentheses": "()",
    "default": "[]",
    "none": ["", ""],
}


def _tag_is(el, tag):
    return el.tag == "{%s}%s" % (NAMESPACES["cd"], tag)


def _translate_name(s):
    if s[:2] == "cd" and s[2:3] in ".:":
        if s[3:] == "sign":
            return "[+-]"
        else:
            return s[3:].upper()
    else:
        return s


def _translate_constant(el):
    join = JOIN_STYLES.get(el.get("method", "none"), "")
    pre = _translate_name(el.get("prefix", ""))
    type_ = _translate_name(el.get("type"))
    content = pre + join + type_
    if el.get("default") == "yes":
        return {"content": content, "default": True}
    else:
        return content


def _iter_power_set(iter_):
    list_ = list(iter_)
    return itertools.chain.from_iterable(
        itertools.combinations(list_, n) for n in range(len(list_) + 1)
    )


def handle_sub_element(el, defs):
    if _tag_is(el, "constant"):
        return _translate_constant(el)
    elif _tag_is(el, "inherit"):
        return "inherits: \\" + el.attrib.get("name")
    elif _tag_is(el, "resolve"):
        for d in defs:
            if d.get("name") == el.get("name"):
                d.tag = "{%s}keywords" % NAMESPACES["cd"]
                return handle_syntax_element(d, defs).get("description")
        return ""
    else:
        raise Exception('unknown tag "{}" in keywords list'.format(el.tag))


def handle_keywords(el, defs):
    mid = "...,..." if el.get("list") == "yes" else "..."
    delim = DELIMITERS.get(el.get("delimiters", "default"), "[]")
    desc = []
    for child in el:
        sub_el = handle_sub_element(child, defs)
        if isinstance(sub_el, list):
            desc += sub_el
        else:
            desc.append(sub_el)
    return {
        "description": desc,
        "inherits": None,
        "optional": el.get("optional") == "yes",
        "rendering": delim[0] + mid + delim[1],
    }


def handle_assignments(el, defs):
    mid = "..,..=..,.." if el.get("list") == "yes" else "..=.."
    delim = DELIMITERS.get(el.get("delimiters", "default"), "[]")
    desc = collections.OrderedDict()
    in_ = None
    for i, child in enumerate(el):
        if _tag_is(child, "parameter"):
            list_ = []
            for param in child:
                sub_el = handle_sub_element(param, defs)
                if isinstance(sub_el, list):
                    list_ += sub_el
                else:
                    list_.append(sub_el)
            desc[_translate_name(child.get("name"))] = list_
        elif _tag_is(child, "inherit"):
            in_ = child.get("name")
        else:
            message = 'unexpected child tag "{}" in element "{}"'
            raise Exception(message.format(child.tag, el))
    return {
        "description": desc,
        "inherits": in_,
        "optional": el.get("optional") == "yes",
        "rendering": delim[0] + mid + delim[1],
    }


def handle_delimiter(el):
    name = el.get("name")
    return {
        "description": None,
        "inherits": None,
        "optional": el.get("optional") == "yes",
        "rendering": "\\" + name if name.isalpha() else name,
    }


def handle_resolve(el, defs):
    for d in defs:
        if d.get("name") == el.get("name"):
            return handle_syntax_element(d[0], defs)
    raise Exception('can\'t resolve argument "{}"'.format(el.get("name")))


def define_generic_handler(desc, rend):
    return lambda element: {
        "description": desc,
        "inherits": None,
        "optional": element.get("optional") == "yes",
        "rendering": rend,
    }


def handle_syntax_element(el, defs):
    handlers = {
        "keywords": lambda e: handle_keywords(e, defs),
        "assignments": lambda e: handle_assignments(e, defs),
        "content": define_generic_handler("CONTENT", "{...}"),
        "csname": define_generic_handler("CSNAME", "\\..."),
        "text": define_generic_handler("TEXT", "..."),
        "angles": define_generic_handler("CONTENT", "<<...>>"),
        "template": define_generic_handler("TEMPLATE", "[|...|]"),
        "triplet": define_generic_handler("TRIPLET", "[x:y:z,..]"),
        "position": define_generic_handler("POSITION", "(...,...)"),
        "index": define_generic_handler("INDEX", "[..+...+..]"),
        "apply": define_generic_handler("APPLY", "[..,..=>..,..]"),
        "resolve": lambda e: handle_resolve(e, defs),
        "delimiter": handle_delimiter,
    }
    for tag, handler in handlers.items():
        if _tag_is(el, tag):
            return handler(el)
    raise Exception('unknown argument type "{}"'.format(el.tag))


def fix_tree(root):
    query = './cd:command//cd:resolve[@name="keyword-name-optional-list"]'
    for cmd in root.findall(query, namespaces=NAMESPACES):
        cmd.set("name", "keyword-name-list-optional")
    for arg in [
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
    ]:
        root.append(ET.fromstring(arg))


def parse_command_instance(el, defs):
    cmd = {
        "name": None,
        "syntax": [],
        "file": el.get("file"),
    }
    args = el.find("./cd:arguments", namespaces=NAMESPACES)
    if args:
        for arg in args:
            cmd["syntax"].append(handle_syntax_element(arg, defs))
    if el.get("type") == "environment":
        cmd["name"] = el.get("begin", "start") + el.get("name")
        close = el.get("end", "stop") + el.get("name")
        cmd["syntax"] += [
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
                "rendering": "\\" + close,
            }
        ]
        close_cmd = {
            "file": el.get("file"),
            "name": close,
            "syntax": [],
        }
        return [cmd, close_cmd]
    else:
        cmd["name"] = el.attrib.get("name")
        return [cmd]


def parse_context_tree(xml):
    defs = [
        child for child in xml.getroot().iterfind(
            "./cd:define", namespaces=NAMESPACES
        )
    ]
    all_cmds = [
        child for child in xml.getroot().iterfind(
            "./cd:command", namespaces=NAMESPACES
        )
    ]
    cmds = {}
    for cmd in all_cmds:
        try:
            for inst in parse_command_instance(cmd, defs):
                name = inst.get("name")
                syntax = inst.get("syntax")

                if name not in cmds:
                    cmds[name] = {
                        "syntax_variants": [syntax],
                        "files": [inst.get("file")],
                    }
                elif not any(
                    syntax == prev
                    for prev in cmds.get(name, {}).get("syntax_variants")
                ):
                    cmds.get(name, {}).get(
                        "syntax_variants", []).append(syntax)
                    if inst.get("file") not in cmds.get(
                            name, {}).get("files", []):
                        cmds.get(name, {}).get(
                            "files", []).append(inst.get("file"))
        except Exception as e:
            message = 'While parsing command "{}" got error "{}"'
            print(message.format(cmd.get("name"), e))
    return cmds


def _translate_keyword(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        if obj.get("default"):
            return "<u>{}</u>".format(obj.get("content"))
        else:
            return obj.get("content")
    else:
        raise Exception('unexpected entry of type "{}"'.format(type(obj)))


def _len(s):
    return len(s.replace("<u>", "").replace("</u>", ""))


def _split(s, limit, max_parts=None):
    if isinstance(max_parts, int):
        if max_parts <= 1:
            return [s]
        else:
            parts = s.split()
            if len(parts) > 1:
                result = [parts[0]]
                for i, part in enumerate(parts[1:]):
                    if len(result) < max_parts:
                        if _len(result[-1] + part) + 1 > limit:
                            result.append(part)
                        else:
                            result[-1] += " " + part
                    else:
                        result[-1] += " " + " ".join(p for p in parts[i + 1:])
                        break
                return result
            else:
                return parts
    else:
        parts = s.split()
        if len(parts) > 1:
            result = [parts[0]]
            for i, part in enumerate(parts[1:]):
                if _len(result[-1] + part) + 1 > limit:
                    result.append(part)
                else:
                    result[-1] += " " + part
            return result
        else:
            return parts


def _sorted(list_):
    def _key(obj):
        return obj.get("content") if isinstance(obj, dict) else obj

    lower = []
    mixed = []
    upper = []
    for e in list_:
        if not any(c in string.ascii_uppercase for c in e):
            lower.append(e)
        elif not all(c in string.ascii_uppercase for c in e):
            mixed.append(e)
        else:
            upper.append(e)
    return (
        sorted(lower, key=_key) + sorted(mixed, key=_key) +
        sorted(upper, key=_key)
    )


def _process_str(desc, lines, first, next_, break_=None):
    if break_ and isinstance(break_, int):
        parts = _split(desc, break_, max_parts=2)
        if len(parts) > 0:
            lines.append(first + parts[0])
            if len(parts) > 1:
                next_parts = _split(parts[1], break_)
                for i, part in enumerate(next_parts):
                    lines.append(next_ + part)
    else:
        lines.append(first + desc)


def _process_list(desc, n, lines, break_=None, sort_lists=False):
    if len(desc) > 0:
        iter_ = _sorted(desc) if sort_lists else desc
        _process_str(
            " ".join(_translate_keyword(item) for item in iter_),
            lines,
            "{:<2}  ".format(n),
            "    ",
            break_=(break_ - 4) if isinstance(break_, int) else break_
        )


def _process_dict(
    desc, n, lines, break_=None, sort_keys=False, sort_lists=False
):
    if len(desc) == 0:
        return
    max_ = max(len(cmd) for cmd in desc)
    template = "{:<%s} = " % max_
    rest = " " * (max_ + 7)
    line_break = (break_ - max_ - 7) if isinstance(break_, int) else break_

    def _init(i, k):
        if i > 0:
            return "    " + template.format(k)
        else:
            return ("{:<2}  " + template).format(n, k)

    i = 0
    iter_ = sorted(desc.items()) if sort_keys else desc.items()
    for key, val in iter_:
        if isinstance(val, str):
            _process_str(val, lines, _init(i, key), rest, break_=line_break)
        elif isinstance(val, list):
            list_iter = _sorted(val) if sort_lists else val
            _process_str(
                " ".join(_translate_keyword(e) for e in list_iter),
                lines,
                _init(i, key),
                rest,
                break_=line_break
            )
        elif isinstance(val, dict):
            _process_str(
                _translate_keyword(val),
                lines,
                _init(i, key),
                rest,
                break_=line_break
            )
        else:
            message = 'unexpected entry of type "{}" in argument "{}"'
            raise Exception(message.format(type(val), key))
        i += 1


def _inherit_str(inherits, n, lines, break_=None):
    if len(lines) > 0:
        _process_str(
            "inherits: \\" + inherits, lines, "    ", "    ", break_=break_
        )
    else:
        _process_str(
            "inherits: \\" + inherits,
            lines,
            "{:<2}  ".format(n),
            "    ",
            break_=break_
        )


def _inherit_list(inherits, n, lines, break_=None, sort_lists=False):
    inheritance = _sorted(inherits) if sort_lists else inherits
    for in_ in inheritance:
        if len(lines) > 0:
            _process_str(
                "inherits: \\" + in_, lines, "    ", "    ", break_=break_
            )
        else:
            _process_str(
                "inherits: \\" + in_,
                lines,
                "{:<2}  ".format(n),
                "    ",
                break_=break_
            )


def rendered_command(
    name, dict_, break_=None, sort_keys=False, sort_lists=False
):
    result = []
    for syntax in dict_.get("syntax_variants", []):
        s = [None] * 3
        s[1] = "\\" + name
        s[0] = " " * len(s[1])
        s[2] = " " * len(s[1])
        doc = []
        if syntax:
            n = 1
            for var in syntax:
                desc = var.get("description")
                inherits = var.get("inherits")
                string = var.get("rendering")
                len_ = len(string)
                if desc is None and inherits is None:
                    s[0] += " " * (len_ + 1)
                    s[1] += " " + string
                    s[2] += " " * (len_ + 1)
                else:
                    lines = []
                    s[1] += " " + string
                    if len_ > 3:
                        temp = "  {:^%s}" % (len_ - 1)
                        s[0] += temp.format(n)
                        s[2] += temp.format("OPT" if var["optional"] else "")
                    else:
                        temp = " {:^%s}" % len_
                        s[0] += temp.format(n)
                        s[2] += temp.format("OPT" if var["optional"] else "")
                    if isinstance(desc, str):
                        _process_str(
                            desc,
                            lines,
                            "{:<2}  ".format(n),
                            "    ",
                            break_=break_
                        )
                    elif isinstance(desc, list):
                        _process_list(
                            desc,
                            n,
                            lines,
                            break_=break_,
                            sort_lists=sort_lists
                        )
                    elif isinstance(desc, dict):
                        _process_dict(
                            desc,
                            n,
                            lines,
                            break_=break_,
                            sort_keys=sort_keys,
                            sort_lists=sort_lists
                        )
                    else:
                        msg = 'unexpected argument of type "{}"'
                        raise Exception(msg.format(type(desc)))

                    if inherits is None:
                        pass
                    elif isinstance(inherits, str):
                        _inherit_str(inherits, n, lines, break_=break_)
                    elif isinstance(inherits, list):
                        _inherit_list(
                            inherits,
                            n,
                            lines,
                            break_=break_,
                            sort_lists=sort_lists
                        )
                    else:
                        msg = "unexpected inheritance of type '{}'"
                        raise Exception(msg.format(type(inherits)))

                    doc.append(lines)
                    n += 1
        for i in range(2, -1, -1):
            s[i] = s[i].rstrip()
            if len(s[i]) == 0:
                del s[i]
        result.append([
            "\n".join(s), "\n\n".join("\n".join(lines) for lines in doc)
        ])
    return sorted(result), dict_.get("files")


def simplified_syntax_variants(variants):
    len_ = len(variants)
    if len_ <= 1:
        return variants
    var_copy = copy.deepcopy(variants)

    def _iter_without_opt_vars(syntax):
        len_ = len(syntax)
        opt_ind = [i for i in range(len_) if syntax[i]["optional"]]
        mand_ind = [i for i in range(len_) if i not in opt_ind]
        for comb in _iter_power_set(opt_ind):
            ind = set(comb)
            ind.update(mand_ind)
            yield [syntax[i] for i in sorted(ind)]

    def _iter_mand_to_opt_vars(syntax):
        mand_ind = [i for i in range(len(syntax)) if not syntax[i]["optional"]]
        copy_ = copy.deepcopy(syntax)
        for comb in _iter_power_set(mand_ind):
            for i in mand_ind:
                copy_[i]["optional"] = True if i in comb else False
            yield copy_

    def _is_copy_without_opt(other, master):
        return any(
            reduced == other for reduced in _iter_without_opt_vars(master)
        )

    done = False
    while not done:
        done = True
        for pair in list(itertools.permutations(
            [(n, entry) for n, entry in enumerate(var_copy)], 2
        )):
            i, master = pair[0]
            j, other = pair[1]
            redundant = False
            for master_var in _iter_mand_to_opt_vars(master):
                if _is_copy_without_opt(other, master_var):
                    redundant = True
                    var_copy[i] = master_var
                    del var_copy[j]
                    break
            if redundant:
                done = False
                break
    return var_copy


def simplify_commands(cmds):
    for name, cmd in cmds.items():
        cmd["syntax_variants"] = \
            simplified_syntax_variants(cmd["syntax_variants"])


def collect(xml, path):
    for f_ in os.listdir(os.path.abspath(path)):
        with open(os.path.join(path, f_), encoding="utf-8") as f:
            try:
                if not f_.endswith(".xml"):
                    pass
                elif f_ in ["i-context.xml", "i-common-definitions.xml"]:
                    pass
                elif xml is None:
                    xml = ET.parse(f)
                else:
                    root = xml.getroot()
                    for e in ET.parse(f).getroot():
                        if f_.startswith("i-common"):
                            root.append(e)
                        elif e.attrib.get("file") is not None:
                            root.append(e)
                        else:
                            e.set("file", f_)
                            root.append(e)
            except ET.ParseError as err:
                msg = (
                    'error "{}" occurred whilst processing file "{}" located '
                    'at "{}"'
                )
                print(msg.format(err, f_, path))
    return xml
