import json
import io
import re

def load_replacements():
    # The tricks I know to make the syntax highlighting work (in Monokai
    # Extended):
    #   'string' - (light) yellow
    #   'variable.parameter' - orange, italic
    #   'keyword' - red
    #   'markup.bold' - red, bold
    #   'markup.italic' - red, italic
    #   'markup.heading' - orange
    #   'constant.(other|numeric|character|...)' - purple
    #   'support.function' (or 'meta.diff'?) - blue
    #   'entity' - green
    #   'comment' - grey(ed out)
    #   'support.entity' - green, italic
    # Honestly though this facet of the syntax highlighting is the one I least
    # understand... looking at the scopes that come up in markdown
    # highlighting, I see a lot of interesting things.
    #   If I get round to adding snippets and other such fancy things to
    # ConTeXtTools, then I'll have to rework this stuff.
    with io.open("syntax_pre_process.json") as f:
        return json.load(f)

def pre_process(pre, post):
    repl = load_replacements()
    with io.open(pre, mode="r", encoding="utf-8") as pre_file:
        with io.open(post, mode="w", encoding="utf-8") as post_file:
            for line in pre_file.readlines():
                # It would be nice, although not really necessary, to clean up
                # the comments while we're here.
                #full_comment_pattern = r"\s*#.*"
                #partial_comment_pattern = r"(.*?[^\\]+?(\\\\)*?)#.*"
                #if re.match(full_comment_pattern, line):
                #    continue
                #elif re.search(partial_comment_pattern, line):
                #    line = re.sub(partial_comment_pattern, r"\1", line)
                for before, after in repl.items():
                    replace_pattern = "{{@%s}}" % before
                    if re.search(replace_pattern, line):
                        line = re.sub(replace_pattern, after, line)
                post_file.write(line)

def main():
    pre_process("ConTeXt.sublime-syntax.pre", "ConTeXt.sublime-syntax")

if __name__ == "__main__":
    main()
