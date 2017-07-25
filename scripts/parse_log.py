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


def parse_lines(bytes_, decode=True):
    if decode:
        string = bytes_.decode(encoding="utf-8", errors="replace").replace(
            "\r\n", "\n").replace("\r", "\n")
    else:
        string = bytes_
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
    tex, lua, mp, other = [], [], [], []
    war, info = {}, {}
    d = parse_lines(bytes_, decode=decode)

    for k, v in d.items():
        if k == "tex error":
            for s in v:
                head = re.search(r"([a-zA-Z]+) error on line ([0-9]+)", s)
                if head:
                    if head.group(1) == "tex":
                        dets = re.search(r"! (.*?)\n", s[head.end():])
                        tex.append({
                            "details": dets.group(1) if dets else None,
                            "line": int(head.group(2))
                        })
                    elif head.group(1) == "mp":
                        dets = re.search(r"! (.*?)\n", s[head.end():])
                        mp.append({
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
                    lua.append({
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

    return {
        "errors": {
            "TeX": utilities.deduplicate(tex),
            "Lua": utilities.deduplicate(lua),
            "MetaPost": utilities.deduplicate(mp),
            "Other": utilities.deduplicate(other)
        },
        "warnings": war,
        "info": info
    }
