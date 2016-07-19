import json
import io
import re

# --- general nested dict functions ---
def iter_deep(dict_, sep=", "):
    for k, v in dict_.items():
        if isinstance(v, dict):
            for key, val in iter_deep(v, sep=sep):
                yield k + sep + key, val
        else:
            yield k, v

def get_deep(dict_, keys):
    if len(keys) <= 1:
        return dict_[keys[0]]
    try:
        return get_deep(dict_[keys[0]], keys[1:])
    except KeyError as e:
        print(keys)
        raise e

def set_deep(dict_, keys, value):
    if len(keys) > 1:
        set_deep(dict_[keys[0]], keys[1:], value)
    else:
        dict_[keys[0]] = value

# --- functions for normalizing the json.pre ---
def uncomment_json(json_str):
    json_str = re.sub(
        r"[ ]*/\*.*?\*/[ ]*\n",
        r"\n",
        json_str,
        flags=re.MULTILINE | re.DOTALL)
    json_str = re.sub(
        r"[ ]*//.*?\n",
        r"\n",
        json_str)
    json_str = re.sub(
        r"^[ ]*\n",
        r"",
        json_str,
        flags=re.MULTILINE)
    return json_str

def sanitize_json_commas(json_str):
    json_str = re.sub(
        r",(\s*?[\]}])",
        r"\1",
        json_str,
        flags=re.MULTILINE)
    return json_str

def dereference_json(json_dict, root="~", dir_sep="/", prev_dir=".."):
    def get_reference(cur_dir, entry):
        match = re.match(r"(.*?){{(.*?)}}(.*)", entry)
        if match:
            pre, ref, post = [match.group(i) for i in {1, 2, 3}]
            new_dir = cur_dir[:-1]
            for part in ref.split(dir_sep):
                if part == root:
                    new_dir = []
                elif part == prev_dir:
                    new_dir.pop()
                else:
                    new_dir.append(part)
            return get_reference(
                new_dir,
                pre + get_deep(json_dict, new_dir) + post)
        else:
            return entry
    sep = "__sep__"
    for keys, entry in iter_deep(json_dict, sep):
        location = keys.split(sep)
        try:
            set_deep(json_dict, location, get_reference(location, entry))
        except KeyError as e:
            print(location, entry)
            raise e
    return json_dict

def load_replacements(file_name):
    with io.open(file_name) as f:
        file_as_str = f.read()
        file_as_str = uncomment_json(file_as_str)
        file_as_str = sanitize_json_commas(file_as_str)
        try:
            replacement_dict = json.loads(file_as_str)
        except ValueError as e:
            print("current state of file:\n", file_as_str)
            raise e
        replacement_dict = dereference_json(replacement_dict)
        return replacement_dict

# --- pre processing the syntax files ---
def uncomment_yaml(yaml_str):
    yaml_str = re.sub(
        r"(?<=[^\\])(\\\\)*#.*?\n",
        r"\n",
        yaml_str,
        flags=re.MULTILINE)
    yaml_str = re.sub(
        r"^[ ]*\n",
        r"",
        yaml_str,
        flags=re.MULTILINE)
    return yaml_str

def dereference_yaml(yaml_str, ref_dict, sep=".", prefix="@"):
    sep_ = "__sep__"
    for keys, val in iter_deep(ref_dict, sep=sep):
        yaml_str = yaml_str.replace(
            "{{%s%s}}" % (prefix, sep.join(keys.split(sep_))),
            val)
    return yaml_str

def pre_process(pre, post, replace_file, sep=".", prefix="@"):
    repl = load_replacements(replace_file)
    with io.open(pre, mode="r") as pre_file:
        with io.open(post, mode="w") as post_file:
            input_str = pre_file.read()
            input_str = uncomment_yaml(input_str)
            input_str = dereference_yaml(
                input_str,
                repl,
                sep=sep,
                prefix=prefix)
            post_file.write(input_str)

# --- main ---
def main():
    pre_process(
        "ConTeXt.sublime-syntax.pre",
        "ConTeXt.sublime-syntax",
        "syntax.json.pre",
        sep="/",
        prefix="!")
    pre_process(
        "ConTeXt Log.sublime-syntax.pre",
        "ConTeXt Log.sublime-syntax",
        "syntax.json.pre",
        sep="/",
        prefix="!")

if __name__ == "__main__":
    main()
