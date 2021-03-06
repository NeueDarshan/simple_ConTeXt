from typing import Optional, Tuple

import sublime


def is_scope(view: sublime.View, scope: str) -> bool:
    sel = view.sel()
    try:
        return view.match_selector(sel[0].begin(), scope)
    except IndexError:
        # If in doubt, let's return `False`.
        return False


def is_context(view: sublime.View) -> bool:
    return is_scope(view, "text.tex.context")


def is_metapost(view: sublime.View) -> bool:
    return is_scope(view, "source.metapost")


def is_lua(view: sublime.View) -> bool:
    return is_scope(view, "source.lua")


# Does order matter for scope matching? If so, then we need to rethink these.
def AND(a: str, b: str) -> str:
    return ALL(a, b)


def ALL(*args: str) -> str:
    return " ".join(args)


def OR(a: str, b: str) -> str:
    return ANY(a, b)


def ANY(*args: str) -> str:
    return ", ".join(args)


def NOT(a: str) -> str:
    return "- {}".format(a)


BACKSLASH = "punctuation.definition.backslash.context"

FULL_START = "meta.structure.start.context"

START = AND(FULL_START, NOT(BACKSLASH))

FULL_STOP = "meta.structure.stop.context"

STOP = AND(FULL_STOP, NOT(BACKSLASH))

FULL_CONTROL_WORD = "meta.control-word.context"

CONTROL_WORD = AND(FULL_CONTROL_WORD, NOT(BACKSLASH))

NOT_CONTROL_WORD = NOT(CONTROL_WORD)

FULL_CONTROL_SYMBOL = "constant.character.escape.context"

CONTROL_SYMBOL = AND(FULL_CONTROL_SYMBOL, NOT(BACKSLASH))

CONTROL_SEQ = OR(CONTROL_WORD, CONTROL_SYMBOL)

FULL_CONTROL_SEQ = OR(FULL_CONTROL_WORD, FULL_CONTROL_SYMBOL)

BEGIN_BRACKET = "punctuation.section.brackets.begin.context"

END_BRACKET = "punctuation.section.brackets.end.context"

BRACKETS = "meta.brackets.context"

BEGIN_BRACE = "punctuation.section.braces.begin.context"

END_BRACE = "punctuation.section.braces.end.context"

BRACES = "meta.braces.context"

ARGUMENT = OR(BRACKETS, BRACES)

NOT_ARGUMENT = NOT(ARGUMENT)

META_ARGUMENT = "meta.environment.argument.context"

KEY = "variable.parameter.context"

EQUALS = "keyword.operator.assignment.context"

VALUE = "meta.value.context"

BRACKETS_NOT_VALUE = AND(BRACKETS, NOT(VALUE))

ASSIGNMENT = ANY(KEY, EQUALS, VALUE)

REFERENCE = "entity.name.label.reference.context"

MAYBE_CITATION = "meta.maybe-citation.context"

FILE_NAME = "meta.file-name.context"

DEFINE_TEX = "entity.name.function.context"

DEFINE_CONTEXT = "entity.name.function.other.context"

DEFINE = OR(DEFINE_TEX, DEFINE_CONTEXT)

DOCUMENT = "entity.name.section.document.context"

OTHER = "entity.name.section.other.context"

PART = "entity.name.section.part.context"

CHAPTER = "entity.name.section.chapter.context"

SECTION = "entity.name.section.section.context"

SUBSECTION = "entity.name.section.subsection.context"

SUB2SECTION = "entity.name.section.sub2section.context"

SUB3SECTION = "entity.name.section.sub3section.context"

SUB4SECTION = "entity.name.section.sub4section.context"

HEADING = ANY(
    # DOCUMENT, OTHER,
    PART, CHAPTER, SECTION, SUBSECTION, SUB2SECTION, SUB3SECTION, SUB4SECTION
)

KEYWORD_BACKSLASH = AND(BACKSLASH, "punctuation.definition.keyword.context")

META_ARGUMENT = "meta.environment.argument.context"

BRACES_ARGUMENT = AND(BRACES, META_ARGUMENT)

BRACKETS_ARGUMENT = AND(BRACKETS, META_ARGUMENT)

META_TITLE = "meta.title.context"

SUPPORT_CONTROL = "support.function.context"

KEYWORD_CONTROL = "keyword.control.context"

KEYWORD_OPERATOR = "keyword.operator.context"

ALIGN_CONTROL = "keyword.operator.alignment.context"

IMPORT_CONTROL = "keyword.control.import.context"

DEFINE_CONTROL = "storage.type.context"

MODIFY_CONTROL = "storage.modifier.context"

CONDITIONAL_CONTROL = "keyword.control.conditional.context"

CONTROL_WORD_NORMAL = AND(FULL_CONTROL_WORD, SUPPORT_CONTROL)

CONTROL_WORD_OPERATOR = AND(FULL_CONTROL_WORD, KEYWORD_OPERATOR)

CONTROL_WORD_START = ALL(FULL_CONTROL_WORD, FULL_START, KEYWORD_CONTROL)

CONTROL_WORD_STOP = ALL(FULL_CONTROL_WORD, FULL_STOP, KEYWORD_CONTROL)

CONTROL_WORD_ALIGN = AND(FULL_CONTROL_WORD, ALIGN_CONTROL)

CONTROL_WORD_IMPORT = AND(FULL_CONTROL_WORD, IMPORT_CONTROL)

CONTROL_WORD_DEFINE = AND(FULL_CONTROL_WORD, DEFINE_CONTROL)

CONTROL_WORD_MODIFY = AND(FULL_CONTROL_WORD, MODIFY_CONTROL)

CONTROL_WORD_CONDITIONAL = AND(FULL_CONTROL_WORD, CONDITIONAL_CONTROL)

EMPHASIS = "markup.italic.emphasis.context"

BOLDFACE = "markup.bold.boldface.context"

ITALIC = "markup.italic.italic.context"

SLANTED = "markup.italic.slanted.context"

BOLD_ITALIC = AND(ITALIC, BOLDFACE)

BOLD_SLANTED = AND(SLANTED, BOLDFACE)

SANS_BOLD = "markup.bold.boldface.context"

TYPEWRITER = "markup.raw.inline.context"

TYPEWRITER_BOLD = AND(BOLDFACE, TYPEWRITER)

EMBEDDED_METAFUN = "source.metapost.metafun.embedded.context"

BLOCK_QUOTE = "markup.quote.block.context"

BLOCK_NOTE = "markup.other.footnote.context"

BLOCK_RAW = "markup.raw.block.context"

MARKUP_HEADING = "markup.heading.context"

BUFFER = "meta.buffer-name.context"


def enclosing_block(
    view: sublime.View, point: int, scope: str, end: Optional[int] = None,
) -> Optional[Tuple[int, int]]:
    start = stop = point
    while start > 0 and view.match_selector(start, scope):
        start -= 1
    end_ = view.size() if end is None else end
    while stop < end_ and view.match_selector(stop, scope):
        stop += 1

    if start < stop:
        return start + 1, stop
    return None


def left_enclosing_block(
    view: sublime.View, point: int, scope: str, end: Optional[int] = None,
) -> Optional[Tuple[int, int]]:
    """
    Like `enclosing_block`, but checks that `point` is the right-boundary of
    the eventual block. If not, signal an error with `None`.
    """

    if end is None:
        end = view.size()
    block = enclosing_block(view, point, scope, end=end)
    if block and not view.match_selector(point + 1, scope):
        return block
    return None


def do_skip_anything(view: sublime.View, point: int) -> bool:
    return True


def do_skip_nothing(view: sublime.View, point: int) -> bool:
    return False


def do_skip_args_and_spaces(view: sublime.View, point: int) -> bool:
    if view.substr(point).isspace() or view.match_selector(point, ARGUMENT):
        return True
    return False


SKIP_ANYTHING = 0

SKIP_NOTHING = 1

SKIP_ARGS_AND_SPACES = 2

SKIPPERS = {
    SKIP_ANYTHING: do_skip_anything,
    SKIP_NOTHING: do_skip_nothing,
    SKIP_ARGS_AND_SPACES: do_skip_args_and_spaces,
}


def last_block_in_region(
    view: sublime.View,
    begin: int,
    scope: str,
    end: Optional[int] = None,
    skip: int = SKIP_ANYTHING,
) -> Optional[Tuple[int, int]]:
    skipper = SKIPPERS.get(skip, do_skip_anything)
    stop = view.size() if end is None else end
    empty = True

    while (
        stop > begin and
        not view.match_selector(stop, scope) and
        skipper(view, stop)
    ):
        stop -= 1

    start = stop
    while start > begin and view.match_selector(start, scope):
        start -= 1
        empty = False

    if empty:
        return None
    return start + 1, stop + 1
