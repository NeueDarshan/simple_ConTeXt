# Simple ConTeXt

## Contents

<!-- MarkdownTOC autolink="true" style="unordered" -->

- [Introduction](#introduction)
- [Installation/Setup](#installationsetup)
  - [Builder](#builder)
  - [PDFs](#pdfs)
  - [Auto-Completion](#auto-completion)
  - [Symbol List](#symbol-list)
  - [Spell Checking](#spell-checking)
  - [Bracket Highlighter](#bracket-highlighter)
- [Builders](#builders)
- [Misc](#misc)
- [Features To Work On](#features-to-work-on)
- [Future Features](#future-features)

<!-- /MarkdownTOC -->

## Introduction

This [Sublime Text][sublime-text] 3 package provides some support for working
with the [ConTeXt][context-introduction] program.

I started this project for my personal use, because I wanted some quality of
life features for writing ConTeXt documents in Sublime Text. Since there were no
packages that fit the bill, I started to write my own. Over time I felt that the
result was looking pretty good, so I put it out into the world for the hopeful
benefit of other ConTeXt users.

That said, I can only test that things work on my machine, so some bugs are to
be expected. Furthermore I only have so much spare time to work on it, and it's
a hobby project. Don't expect a robust, polished experience!

Currently the features are:

- Syntax file(s).
- Builder(s).
- Command auto-completions.
- Command pop-ups.
- Handling of references. (Not citations.)
- Snippets.
- Other miscellany.

## Installation/Setup

Install via [package control][package-control], under the name `simple_ConTeXt`.
Afterwards, there are some optional things to set up.

### Builder

Open the simple ConTeXt settings file via `Preferences: simple_ConTeXt Settings`
in the command palette or
`Preferences ▶ Package Settings ▶ simple_ConTeXt ▶ Settings` in the menu bar.
Under the `paths` key, put in a key-value entry for the ConTeXt installation on
your machine: the key is just a name for that installation, and the value should
be the path to the `context` binaries. For example: if you have the `context`
program located at
`/home/user-name/.local/context/tex/texmf-linux-64/bin/context` (so the ConTeXt
installation tree's root is at `/home/user-name/.local/context/`), then you
should write something like

```json
{
  "program_locations": {
    "ConTeXt_paths": {
      "example": "/home/user-name/.local/context/tex/texmf-linux-64/bin"
    }
  }
}
```

If you have multiple versions of ConTeXt installed (e.g. a couple different TeX
Live versions and the ConTeXt Standalone) then you can put a name-path entry for
each one, and they can happily coexist in simple ConTeXt.

### PDFs

For opening PDFs after building a ConTeXt file, and for opening the manuals, the
`current_settings ▶ PDF ▶ viewer` entry is consulted. It should be the name of
one of the keys in `program_locations ▶ PDF_viewers`.

Similarly to the previous, the keys in `program_locations ▶ PDF_viewers` can be
any string, but each value should be the name of a PDF viewer program. (In the
case of Sumatra PDF viewer, this could be simply `sumatraPDF` if it's on your
environment path, or else an explicit path like `/usr/bin/sumatraPDF`.)

### Auto-Completion

Add the following entry to your general Sublime Text (ST) settings, in order to
get automatic completions for ConTeXt commands on typing the initial backslash
<kbd>\\</kbd>.

```json
{
  "auto_complete_triggers": [
    {
      "characters": "\\",
      "selector": "text.tex.context"
    }
  ]
}
```

### Symbol List

Consider adding the following to your key bindings: it will (for ConTeXt files
only) replace the binding for the local symbol list
(<kbd>Ctrl</kbd>+<kbd>R</kbd>) with a custom variation of it. The idea is to
make it easier to navigate/filter between headings, definitions, references, and
so on.

```json
{
  "keys": ["ctrl+r"],
  "command": "simple_context_show_combined_overlay",
  "args": {
    "selectors": ["definition", "file_name", "heading", "reference"],
    "active_selectors": ["definition", "file_name", "heading", "reference"]
  },
  "context": [
    {
      "key": "selector",
      "operator": "equal",
      "operand": "text.tex.context"
    }
  ]
}
```

Otherwise, the default local symbol list contains all these things with suitable
prefixes.

### Spell Checking

Consider adding the following to your ConTeXt syntax specific settings:

```json
{
  "spell_check": true,
  "spelling_selector": "text.tex.context - (meta.control-word.context, meta.environment.math.context, meta.brackets.context, source, markup.raw, comment)"
}
```

This should do a pretty decent job at limiting spell check to the appropriate
places only (e.g. not in maths or code blocks).

### Bracket Highlighter

If you use the excellent [BracketHighlighter][bracket-highlighter] package, then
adding the following to the BracketHighlighter settings will provide some
rudimentary support for ConTeXt start/stop commands.

```json
{
  "user_brackets": [
    {
      "name": "context_env",
      "open": "(\\\\start[a-zA-Z]*)",
      "close": "(\\\\stop[a-zA-Z]*)",
      "style": "tag",
      "scope_exclude": ["- meta.structure"],
      "language_filter": "whitelist",
      "language_list": ["ConTeXt"],
      "enabled": true
    }
  ]
}
```

## Builders

The main builder is of course the ConTeXt one, that is a wrapper around the
`context` binary. In order to find `context` it consults the path specified in
the settings.

As it's easy to do so, there are a couple other builders:

- Lua (using LuaTeX as a Lua interpreter);
- MetaPost. There are two variants: firstly, just use the version of `mpost`
  that ships with the ConTeXt installation. Alternatively, use `context` itself:
  when called on a MetaPost file, it will compile it (using the MetaFun format)
  into a PDF.

## Misc

Completions should play well with others, e.g. the completions provided by the
[UnicodeCompletion][unicode-completion] package. (Although UnicodeCompletion is
intended for LaTeX, I still find it useful for ConTeXt as many of the command
names are the same.)

## Features To Work On

Things that should be relatively easy to add at the moment.

- Add option for return focus to ST after opening PDF on build.
- Add option for showing output panel, with the choices:
  - never,
  - only if there are errors/warnings,
  - always.
- Review README.
- Add auto-build functionality. It should have the ability to pass different
  options to the auto-builder, e.g. `--flags=draft`. It should have options for
  when to run:
  - at one or both of:
    - on save,
    - at regular time intervals;
  - never.

## Future Features

Features we would like to have, but may be harder to implement.

- SyncTeX support. (Forward and backward jump to PDF.)
- Code formatter.
- Extend the command auto-complete/pop-up system to allow for user-defined
  commands. Easiest would probably be to define them in the `.xml` style that
  the ConTeXt interface files use.
- Fix up the documentation browser.
- Checker/linter. (The checks provided by `mtxrun --script check` are quite
  basic. Not sure what ConTeXt support `chktex` has.)
- Citation handler. (We handle references well enough, similar support would be
  nice for `\cite[...]`. I expect we would try to keep it simple, and I would
  like to handle the `.lua`, `.xml` and `.bib` formats.)
- Handle syntax embedding better. Currently we have various embeddings that work
  fairly well, but the code is ugly and error prone and comes with some
  limitations.
- Robust log parsing, esp. for reporting warnings/errors.
- Word count. (Could be nice to have, but lots of difficulties with it.)

[context-introduction]: http://wiki.contextgarden.net/What_is_ConTeXt
[package-control]:      https://packagecontrol.io
[sublime-text]:         https://www.sublimetext.com
[unicode-completion]:   https://github.com/randy3k/UnicodeCompletion
[bracket-highlighter]:  https://github.com/facelessuser/BracketHighlighter
