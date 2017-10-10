def is_scope(view, scope):
    return view.match_selector(view.sel()[0].begin(), scope)


def is_context(view):
    return is_scope(view, "text.tex.context")


def is_metapost(view):
    return is_scope(view, "source.metapost")


def is_lua(view):
    return is_scope(view, "source.lua")


def AND(a, b):
    return ALL(a, b)


def ALL(*args):
    return "({})".format(" ".join(args))


def OR(a, b):
    return ANY(a, b)


def ANY(*args):
    return "({})".format(", ".join(args))


def NOT(a):
    return "- ({})".format(a)


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

KEY = "variable.parameter.context"

EQUALS = "keyword.operator.assignment.context"

VALUE = "meta.value.context"

ASSIGNMENT = ANY(KEY, EQUALS, VALUE)

REFERENCE = "entity.name.label.reference.context"

FILE_NAME = "meta.file-name.context"

DEFINE_MAIN = "entity.name.function.context"

DEFINE_OTHER = "entity.name.function.other.context"

DEFINE = OR(DEFINE_MAIN, DEFINE_OTHER)


def skip_while_match(view, begin, end, scope):
    point = begin
    while point < end and view.match_selector(point, scope):
        point += 1
    return point


def skip_while_space(view, begin, end):
    point = begin
    while point < end and view.substr(point).isspace():
        point += 1
    return point


def enclosing_block(view, point, end, scope):
    start = stop = point
    while start > 0 and view.match_selector(start, scope):
        start -= 1
    while stop < end and view.match_selector(stop, scope):
        stop += 1
    if start < stop:
        return [start + 1, stop]
    else:
        return


#D Like \type{enclosing_block}, but checks that \type{point} is the
#D right||boundary of the eventual block. If not, signal an error.
def left_enclosing_block(view, point, end, scope):
    block = enclosing_block(view, point, end, scope)
    if block and not view.match_selector(point + 1, scope):
        return block
    else:
        return


def block_contains_scope(view, begin, end, scope):
    return any(
        view.match_selector(point, scope) for point in range(begin, end)
    )


def all_blocks_in_region(view, begin, end, scope):
    matches = []
    for point in range(begin, end):
        if view.match_selector(point, scope):
            matches.append(point)
    return sorted(
        set(enclosing_block(view, match, scope) for match in matches)
    )


def do_skip_anything(view, point):
    return True


def do_skip_nothing(view, point):
    return False


def do_skip_args_and_spaces(view, point):
    if view.substr(point).isspace() or view.match_selector(point, ARGUMENT):
        return True
    else:
        return False


SKIP_ANYTHING = 0

SKIP_NOTHING = 1

SKIP_ARGS_AND_SPACES = 2

SKIPPERS = {
    SKIP_ANYTHING: do_skip_anything,
    SKIP_NOTHING: do_skip_nothing,
    SKIP_ARGS_AND_SPACES: do_skip_args_and_spaces,
}


def last_block_in_region(view, begin, end, scope, skip=SKIP_ANYTHING):
    skipper = SKIPPERS.get(skip, do_skip_anything)
    stop = end
    empty = True

    while (
        stop > begin and
        not view.match_selector(stop, scope) and
        skipper(view, stop)
    ):
        stop -= 1
        empty = False

    start = stop
    while start > begin and view.match_selector(start, scope):
        start -= 1
        empty = False

    if not empty:
        return [start + 1, stop + 1]
    else:
        return
