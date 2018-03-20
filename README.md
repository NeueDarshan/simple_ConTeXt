# Contents

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

# Introduction

This [Sublime Text][sublime-text] 3 package provides some support for working with the [ConTeXt][context-introduction] program.

I started this project for my personal use, because I wanted some quality of life features for writing ConTeXt documents in Sublime Text. Since there were no packages that fit the bill, I started to write my own. Over time I felt that the result was looking pretty good, so I put it out into the world for the hopeful benefit of other ConTeXt users.

That said, I can only test that things work on my machine, so some bugs are to be expected. Furthermore I only have so much spare time to work on it, and it's a hobby project. Don't expect a robust, polished experience!

Currently the features are:

- Syntax file(s).
- Builder(s).
- Command auto-completions.
- Command pop-ups.
- Handling of references. (Not citations at the moment.)
- Snippets.
- Other bits and bobs.

# Installation/Setup

Install via [package control][package-control], under the name `simple_ConTeXt`. Afterwards, there are some optional things to set up.

## Builder

Open the simple ConTeXt settings file via `Preferences: simple_ConTeXt Settings` in the command palette or `Preferences/Package Settings/simple_ConTeXt/Settings` in the menu bar. Under the `paths` key, put in a key-value entry for the ConTeXt installation on your machine: the key is a name for that installation, and the value should be the path to the context binaries. For example, if you have a ConTeXt distribution installed at `/home/user-name/.local/context/` and the actual context binary is located at `/home/user-name/.local/context/tex/texmf-linux-64/bin/context`, then you should have

```JSON
{
  "paths": {
    "main": "/home/user-name/.local/context/tex/texmf-linux-64/bin"
  }
}
```

If you have multiple versions of ConTeXt installed (e.g. a couple different TeX Live versions and the ConTeXt Standalone) then you can put a name-path entry for each one, and they can happily coexist in simple ConTeXt.

## PDFs

For opening PDFs after building a ConTeXt file, and opening the manuals, the `PDF_viewers` entry is consulted. Similarly to the previous, the keys can be any string, but each value should be the name of a PDF viewer program. (In the case of Sumatra PDF viewer, this could be simply `sumatraPDF` if it's on your environment path, or else an explicit path like `/usr/bin/sumatraPDF`.)

## Auto-Completion

Add the following entry to your general Sublime Text (ST) settings, in order to get automatic completions for ConTeXt commands on typing the initial backslash <kbd>\\</kbd>.

```JSON
{
  "auto_complete_triggers": [
    {
      "characters": "\\",
      "selector": "text.tex.context"
    }
  ]
}
```

## Symbol List

Consider adding the following to your key bindings: it will (for ConTeXt files only) replace the binding for the local symbol list (<kbd>Ctrl</kbd>+<kbd>R</kbd>) with a custom variation of it. The idea is to make it easier to navigate/filter between headings, definitions, references, and so on.

```JSON
{
  "keys": ["ctrl+r"],
  "command": "simple_context_show_combined_overlay",
  "args": {
    "selectors": ["definition", "file_name", "heading", "reference"],
    "active_selectors": ["heading", "reference"]
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

Otherwise, the default local symbol list contains all these things with suitable prefixes.

## Spell Checking

Consider adding the following to your ConTeXt syntax specific settings:

```JSON
{
  "spell_check": true,
  "spelling_selector": "text.tex.context - (meta.control-word.context, meta.environment.math.context, meta.brackets.context, source, markup.raw, comment)"
}
```

This should do a pretty decent job at limiting spell check to the appropriate places only (e.g. not in maths or code blocks).

## Bracket Highlighter

If you use the excellent [BracketHighlighter][bracket-highlighter] package, then adding the following to the BracketHighlighter settings will provide some rudimentary support for ConTeXt start/stop commands.

```JSON
{
  "user_brackets": [
    {
      "name": "context_env",
      "open": "(\\\\start[a-zA-Z]*)",
      "close": "(\\\\stop[a-zA-Z]*)",
      "style": "tag",
      "scope_exclude": ["-meta.structure"],
      "language_filter": "whitelist",
      "language_list": ["ConTeXt"],
      "enabled": true
    }
  ]
}
```

In a similar way, here is an example of some rudimentary MetaPost support for BracketHighlighter.

```JSON
{
  "user_brackets": [
    {
      "name": "metapost_def",
      "open": "(\\b(?:var|(?:prim|second|terti)ary)?def\\b)",
      "close": "(\\benddef\\b)",
      "style": "default",
      "scope_exclude": ["string", "comment"],
      "language_filter": "whitelist",
      "language_list": ["MetaPost", "MetaFun"],
      "enabled": true
    },
    {
      "name": "metapost_env",
      "open": "(\\bbegin(?:fig|group)\\b)",
      "close": "(\\bend(?:fig|group)\\b)",
      "style": "default",
      "scope_exclude": ["string", "comment"],
      "language_filter": "whitelist",
      "language_list": ["MetaPost", "MetaFun"],
      "enabled": true
    },
    {
      "name": "metapost_ctrl",
      "open": "(\\bif\\b)",
      "close": "(\\bfi\\b)",
      "style": "default",
      "scope_exclude": ["string", "comment"],
      "language_filter": "whitelist",
      "language_list": ["MetaPost", "MetaFun"],
      "enabled": true
    },
    {
      "name": "metapost_loop",
      "open": "(\\bfor(?:suffixes|ever)?\\b)",
      "close": "(\\bendfor\\b)",
      "style": "default",
      "scope_exclude": ["string", "comment"],
      "language_filter": "whitelist",
      "language_list": ["MetaPost", "MetaFun"],
      "enabled": true
    }
  ]
}
```

# Builders

The main builder is of course the ConTeXt one, that is a wrapper around the `context` binary. In order to find `context` it consults the path specified in the settings.

As it's easy to do so, there are a couple other builders:

- Lua (using LuaTeX as a Lua interpreter);

- MetaPost. There are two variants: firstly, just use the version of `mpost` that ships with the ConTeXt installation. Alternatively, use `context` itself: when called on a MetaPost file, it will compile it (using the MetaFun format) into a PDF.

# Misc

Completions should play well with others, e.g. the completions provided by the [UnicodeCompletion][unicode-completion] package. (Although UnicodeCompletion is intended for LaTeX, I still find it useful for ConTeXt as many of the command names are the same.)

[context-introduction]: http://wiki.contextgarden.net/What_is_ConTeXt
[package-control]:      https://packagecontrol.io
[sublime-text]:         https://www.sublimetext.com
[unicode-completion]:   https://github.com/randy3k/UnicodeCompletion
[bracket-highlighter]:  https://github.com/facelessuser/BracketHighlighter
