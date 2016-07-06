import json
import io
import re

def load_replacements():
    with io.open("syntax_pre_process.json") as f:
        input_str = f.read()
        input_str = re.sub(
            r"[ ]*//.*?\n",
            r"",
            input_str)
        input_str = re.sub(
            r"/\*.*?\*/\s*\n",
            r"",
            input_str,
            flags=re.MULTILINE | re.DOTALL)
        return json.loads(input_str)

def pre_process(pre, post):
    repl = load_replacements()
    with io.open(pre, mode="r") as pre_file:
        with io.open(post, mode="w") as post_file:
            input_str = pre_file.read()
            input_str = re.sub(
                r"^[ ]*#.*?\n",
                r"",
                input_str,
                flags=re.MULTILINE)
            input_str = re.sub(
                r"^(.*?[^\\])[ ]*#.*?$",
                r"\1",
                input_str,
                flags=re.MULTILINE)
            for before, after in repl.items():
                input_str = re.sub("{{@%s}}" % before, after, input_str)
            post_file.write(input_str)

def main():
    pre_process("ConTeXt.sublime-syntax.pre", "ConTeXt.sublime-syntax")

if __name__ == "__main__":
    main()
