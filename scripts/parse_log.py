import re
from . import utilities


IGNORE = 0

SPECIAL = 1


def categorize(line):
    line = line.strip()
    if not line:
        return IGNORE
    elif not re.match("^([a-zA-Z\s]+?) >(.*?)$", line):
        return SPECIAL
    cats = []
    while True:
        m = re.match("^([a-zA-Z\s]+?) >(.*?)$", line)
        if m:
            cats.append(m.group(1).strip())
            line = m.group(2).strip()
        else:
            break
    if not line:
        return IGNORE
    return cats, line


def append_deep_safe(dict_, keys, value):
    k = "/".join(keys)
    if dict_.get(k) is None:
        dict_[k] = [value]
    else:
        dict_[k].append(value)


def preprocess_lines(s):
    return re.sub(
        r"^((?:Over|Under)full)",
        r"tex warning     > tex warning: bad box\n\1",
        s,
        flags=re.MULTILINE
    )


def parse_lines(bytes_, decode=True):
    if decode:
        string = bytes_.decode(encoding="utf-8", errors="replace").replace(
            "\r\n", "\n").replace("\r", "\n")
    else:
        string = bytes_
    string = preprocess_lines(string)
    log = {}
    prev = None
    for line in string.split("\n"):
        res = categorize(line)
        if res is IGNORE:
            pass
        elif res is SPECIAL:
            if prev:
                append_deep_safe(log, prev, "next:" + line)
        else:
            cats, end_ = res
            prev = cats
            append_deep_safe(log, cats, "init:" + end_)
    return parse_lines_aux(log)


def parse_lines_aux(log):
    d = {}
    for k, v in log.items():
        d[k] = []
        for line in v:
            type_ = line[:4]
            s = line[5:]
            if type_ == "init":
                d[k].append([s])
            else:
                d[k][-1].append(s)
    return {k: ["\n".join(v) for v in d[k]] for k in d}


def parse_log(bytes_, decode=True):
    tex_err, lua_err, mp_err, other_err = [], [], [], []
    tex_war, other_war = [], []
    info = {}
    d = parse_lines(bytes_, decode=decode)

    for k, v in d.items():
        if k == "tex error":
            for s in v:
                head = re.search(r"([a-zA-Z]+) error on line ([0-9]+)", s)
                if head:
                    if head.group(1) == "tex":
                        dets = re.search(r"! (.*?)\n", s[head.end():])
                        tex_err.append({
                            "details": dets.group(1) if dets else None,
                            "line": int(head.group(2))
                        })
                    elif head.group(1) == "mp":
                        dets = re.search(r"! (.*?)\n", s[head.end():])
                        mp_err.append({
                            "details": dets.group(1) if dets else None,
                            "line": int(head.group(2))
                        })
        elif k == "lua error":
            for s in v:
                head = re.search(r"lua error on line ([0-9]+)", s)
                if head:
                    dets = re.search(
                        r"\[ctxlua\]:([0-9]+): (.*?)\n", s[head.end():]
                    )
                    lua_err.append({
                        "details": dets.group(2) if dets else None,
                        "line": int(head.group(1))
                    })
        elif k == "mkiv lua stats":
            for s in v:
                head = re.search(
                    r"runtime: (.*?) seconds, ([0-9]+) processed "
                    r"pages, ([0-9]+) shipped pages, (.*?) pages/second",
                    s
                )
                if head:
                    info["runtime"] = float(head.group(1))
                    info["pages"] = int(head.group(3))
                    info["pages/second"] = float(head.group(4))
        if k == "tex warning":
            for s in v:
                head = re.search(r"tex warning: bad box", s)
                if head:
                    hbox_dets = re.search(
                        r"(Over|Under)full \\hbox \((.*?)\) in paragraph at "
                        r"lines ([0-9]+)\-\-([0-9]+)",
                        s[head.end():]
                    )
                    vbox_dets = re.search(
                        r"(Over|Under)full \\vbox \((.*?)\) detected at line "
                        r"([0-9]+)",
                        s[head.end():]
                    )
                    if hbox_dets:
                        if (
                            int(hbox_dets.group(3)) ==
                            int(hbox_dets.group(4)) - 1
                        ):
                            dets = "line {} > {}full \\hbox ({})"
                            tex_war.append({
                                "details": dets.format(
                                    hbox_dets.group(3),
                                    hbox_dets.group(1).lower(),
                                    hbox_dets.group(2)
                                ),
                                "line": int(hbox_dets.group(3))
                            })
                        else:
                            dets = (
                                "lines {}--{} > {}full \\hbox ({})"
                            )
                            tex_war.append({
                                "details": dets.format(
                                    hbox_dets.group(3),
                                    int(hbox_dets.group(4)) - 1,
                                    hbox_dets.group(1).lower(),
                                    hbox_dets.group(2),
                                ),
                                "line": int(hbox_dets.group(3))
                            })
                    elif vbox_dets:
                        dets = "line {} > {}full \\vbox ({})"
                        tex_war.append({
                            "details": dets.format(
                                vbox_dets.group(3),
                                vbox_dets.group(1).lower(),
                                vbox_dets.group(2)
                            ),
                            "line": int(vbox_dets.group(3))
                        })

    return {
        "errors": {
            "TeX": utilities.deduplicate(tex_err),
            "Lua": utilities.deduplicate(lua_err),
            "MetaPost": utilities.deduplicate(mp_err),
            "Other": utilities.deduplicate(other_err)
        },
        "warnings": {
            "TeX": utilities.deduplicate(tex_war),
            "Other": utilities.deduplicate(other_war)
        },
        "info": info
    }
