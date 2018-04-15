from YAMLMacros.lib.syntax import rule
from YAMLMacros.lib.arguments import argument, foreach, format, if_
from YAMLMacros.lib.extend import apply, merge, prepend

from . import scopes


_MAPS = {
    "heading": {
        "part": r"part",
        "chapter": r"(?:chapter|title)",
        "section": r"(?:section|subject)",
        "subsection": r"sub(?:section|subject)",
        "sub2section": r"subsub(?:section|subject)",
        "sub3section": r"subsubsub(?:section|subject)",
        "sub4section": r"subsubsubsub(?:section|subject)",
    },
    "markup": {
        "emphasis": r"emph",
        "boldface": r"(?:small)?bold",
        "italic": r"italic",
        "slanted": r"(?:small)?slanted",
        "bold-italic": r"(?:small)?(?:bolditalic|italicbold)",
        "bold-slanted": r"(?:small)?(?:boldslanted|slantedbold)",
        "sans-bold": r"sansbold",
        "typewriter": r"mono",
        "typewriter-bold": r"monobold",
    },
    "markup_group": {
        "emphasis": scopes.EMPHASIS,
        "boldface": scopes.BOLDFACE,
        "italic": scopes.ITALIC,
        "slanted": scopes.SLANTED,
        "bold-italic": scopes.BOLD_ITALIC,
        "bold-slanted": scopes.BOLD_SLANTED,
        "sans-bold": scopes.SANS_BOLD,
        "typewriter": scopes.TYPEWRITER,
        "typewriter-bold": scopes.TYPEWRITER_BOLD,
    },
}


def _control_sequence_aux(name, scope, backslash=scopes.BACKSLASH):
    return {
        "match": r"(\\){}\b".format(name),
        "captures": {0: scope, 1: backslash},
    }


def _control_sequence(
    name,
    scope,
    name_map=None,
    name_pre="",
    name_post="",
    backslash=scopes.BACKSLASH,
    **kwargs
):
    if name_map in _MAPS:
        name = _MAPS[name_map].get(name, name)
    rule_base = _control_sequence_aux(
        name_pre + name + name_post, scope, backslash=backslash,
    )
    for k, v in kwargs.items():
        if v is not None:
            rule_base[k] = v
    return rule(**rule_base)


def control_sequence(name="", **kwargs):
    return _control_sequence(name, scopes.CONTROL_WORD_NORMAL, **kwargs)


def control_sequence_start(name="", **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_START, name_pre="start", **kwargs
    )


def control_sequence_stop(name="", **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_STOP, name_pre="stop", **kwargs
    )


def control_sequence_align(name="", **kwargs):
    return _control_sequence(
        name,
        scopes.CONTROL_WORD_ALIGN,
        backslash=scopes.KEYWORD_BACKSLASH,
        **kwargs
    )


def control_sequence_import(name="", **kwargs):
    return _control_sequence(
        name,
        scopes.CONTROL_WORD_IMPORT,
        backslash=scopes.KEYWORD_BACKSLASH,
        **kwargs
    )


def control_sequence_conditional(name="", **kwargs):
    return _control_sequence(
        name,
        scopes.CONTROL_WORD_CONDITIONAL,
        backslash=scopes.KEYWORD_BACKSLASH,
        **kwargs
    )


def control_sequence_define(name="", **kwargs):
    return _control_sequence(name, scopes.CONTROL_WORD_DEFINE, **kwargs)


def control_sequence_modify(name="", **kwargs):
    return _control_sequence(name, scopes.CONTROL_WORD_MODIFY, **kwargs)


def control_sequence_group_markup(name="", push_scoping=None):
    rule_base = {
        "match": r"(\{)\s*((\\)%s)\b" % name,
        "captures": {
            1: scopes.BEGIN_BRACE,
            2: scopes.CONTROL_WORD_NORMAL,
            3: scopes.BACKSLASH,
        },
    }
    if push_scoping is not None:
        rule_base["push"] = "scoping.group.{}.main/".format(push_scoping)
    return rule(**rule_base)


def block_stop(
    name="", meta_content_scope="", meta_include_prototype=None, include=None,
):
    if include is None:
        include_rule = []
    else:
        include_rule = [rule(include=include)]
    if meta_include_prototype is None:
        prototype_rule = []
    else:
        prototype_rule = [rule(meta_include_prototype=meta_include_prototype)]
    return rule(
        match="",
        set=prototype_rule + [
            rule(meta_content_scope=meta_content_scope),
            rule(match=r"(?=\\stop{}\b)".format(name), pop=True),
        ] + include_rule,
    )


def block_stop_quote(name):
    return block_stop(
        name=name, meta_content_scope=scopes.BLOCK_QUOTE, include="main",
    )


def block_stop_verbatim(name):
    return block_stop(
        name=name,
        meta_content_scope=scopes.BLOCK_RAW,
        meta_include_prototype=False,
    )


def list_heading(name):
    content_scope = scopes.ALL(
        scopes.VALUE,
        scopes.META_TITLE,
        "entity.name.section.{}.context".format(name),
        scopes.MARKUP_HEADING,
    )
    return [
        rule(
            match=r"\[",
            scope=scopes.BEGIN_BRACKET,
            set=[
                rule(meta_scope=scopes.BRACKETS_ARGUMENT),
                rule(
                    match=r"\b(title)\s*(=)",
                    captures={1: scopes.KEY, 2: scopes.EQUALS},
                    push=[
                        rule(meta_content_scope=content_scope),
                        rule(include="argument.list.heading.common/"),
                    ],
                ),
                rule(include="argument.list.main/"),
            ],
        ),
        rule(include="generic.pop-if-no-nearby-list/"),
    ]


def group_heading(name):
    content_scope = scopes.ALL(
        scopes.META_TITLE,
        "entity.name.section.{}.context".format(name),
        scopes.MARKUP_HEADING,
    )
    return [
        rule(
            match=r"\{",
            scope=scopes.BEGIN_BRACE,
            set=[
                rule(meta_scope=scopes.BRACES_ARGUMENT),
                rule(meta_content_scope=content_scope.format(name)),
                rule(include="argument.group.main/"),
            ],
        ),
        rule(include="generic.pop-if-no-nearby-group/"),
    ]


def group_markup(name):
    fallback = "markup.italic.{}.context".format(name)
    content_scope = _MAPS["markup_group"].get(name, fallback)
    return [
        rule(
            match=r"\{",
            scope=scopes.BEGIN_BRACE,
            set=[
                rule(meta_scope=scopes.BRACES_ARGUMENT),
                rule(meta_content_scope=content_scope),
                rule(include="argument.group.main/"),
            ],
        ),
        rule(include="generic.pop-if-no-nearby-group/"),
    ]


def assignment(delim="=", mode="list", include_main="main"):
    return rule(
        match="({{key}}*)\\s*(%s)" % delim,
        captures={1: scopes.KEY, 2: scopes.EQUALS},
        push=[
            rule(meta_content_scope=scopes.VALUE),
            rule(include="generic.{}.pop-at-end-of-assignment/".format(mode)),
            rule(include="generic.dimension"),
            rule(include=include_main),
        ],
    )


def verbatim_helper(name="", arg=None):
    if arg is None:
        arg_ = "argument.list*/"
    else:
        arg_ = "argument.list.{}*/".format(arg)
    return rule(
        match="",
        push=["verbatim.main.{}.aux/".format(name), arg_],
    )
