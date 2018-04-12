from YAMLMacros.lib.syntax import rule
from YAMLMacros.lib.arguments import argument, foreach, format, if_
from YAMLMacros.lib.extend import apply, merge, prepend

from . import scopes


_MAP_HEADING = {
    "part": "part",
    "chapter": "(?:chapter|title)",
    "section": "(?:section|subject)",
    "subsection": "sub(?:section|subject)",
    "sub2section": "subsub(?:section|subject)",
    "sub3section": "subsubsub(?:section|subject)",
    "sub4section": "subsubsubsub(?:section|subject)",
}

_MAP_MARKUP = {
    "emphasis": scopes.EMPHASIS,
    "boldface": scopes.BOLDFACE,
    "italic": scopes.ITALIC,
    "slanted": scopes.SLANTED,
    "bold-italic": scopes.BOLD_ITALIC,
    "bold-slanted": scopes.BOLD_SLANTED,
    "sans-bold": scopes.SANS_BOLD,
    "typewriter": scopes.TYPEWRITER,
    "typewriter-bold": scopes.TYPEWRITER_BOLD,
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
    push=None,
    set_=None,
    pop=None,
    backslash=scopes.BACKSLASH,
):
    if name_map == "heading":
        name = _MAP_HEADING.get(name, name)
    elif name_map == "markup":
        name = _MAP_MARKUP.get(name, name)
    rule_base = _control_sequence_aux(
        name_pre + name + name_post, scope, backslash=backslash,
    )
    if push is not None:
        rule_base["push"] = push
    if set_ is not None:
        rule_base["set"] = set_
    if pop is not None:
        rule_base["pop"] = pop
    return rule(**rule_base)


def control_sequence(name="", set=None, **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_NORMAL, set_=set, **kwargs
    )


def control_sequence_start(name="", set=None, **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_START, name_pre="start", set_=set, **kwargs
    )


def control_sequence_stop(name="", set=None, **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_STOP, name_pre="stop", set_=set, **kwargs
    )


def control_sequence_align(name="", set=None, **kwargs):
    return _control_sequence(
        name,
        scopes.CONTROL_WORD_ALIGN,
        backslash=scopes.KEYWORD_BACKSLASH,
        set_=set,
        **kwargs
    )


def control_sequence_import(name="", set=None, **kwargs):
    return _control_sequence(
        name,
        scopes.CONTROL_WORD_IMPORT,
        backslash=scopes.KEYWORD_BACKSLASH,
        set_=set,
        **kwargs
    )


def control_sequence_conditional(name="", set=None, **kwargs):
    return _control_sequence(
        name,
        scopes.CONTROL_WORD_CONDITIONAL,
        backslash=scopes.KEYWORD_BACKSLASH,
        set_=set,
        **kwargs
    )


def control_sequence_define(name="", set=None, **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_DEFINE, set_=set, **kwargs
    )


def control_sequence_modify(name="", set=None, **kwargs):
    return _control_sequence(
        name, scopes.CONTROL_WORD_MODIFY, set_=set, **kwargs
    )


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


def block_stop_metafun(name):
    return block_stop(
        name=name,
        meta_content_scope=scopes.EMBEDDED_METAFUN,
        include="MetaFun.main",
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
    content_scope = \
        _MAP_MARKUP.get(name, "markup.italic.{}.context".format(name))
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
