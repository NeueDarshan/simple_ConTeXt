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
- [Snippets](#snippets)
- [Key/Value Auto-Complete](#keyvalue-auto-complete)
- [Quick Settings](#quick-settings)
- [Scripts](#scripts)
- [Misc](#misc)
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
- Handling of references and citations.
- Snippets.
- Other miscellany.

(I should say that I use ConTeXt MkIV exclusively, and so the package is
designed and tested with MkIV only. In other words, if MkII stuff works then it
is a happy accident. That said, the syntax file should work perfectly well for
MkII, and some of the other parts might still work or be relatively simple to
adapt as needed.

Also, the multilingual interface in ConTeXt is not something I have considered.
I only know the English interface, and have worked with it in mind; the task of
supporting all of the different interfaces simultaneously seems rather daunting
to me.)

## Installation/Setup

Install via [package control][package-control], under the name `simple_ConTeXt`.
(Alternatively, `git clone` the repository into your Sublime Text (ST) packages
directory.) Afterwards, there are some optional things to set up.

### Builder

To get the builder working, it needs to be able to find the `context` program on
your machine. If you have only one version of `context` installed and it's on
your environment `PATH` variable, then you don't need to do anything.

Otherwise, you should tell simple ConTeXt where `context` is located at. To do
so, open the simple ConTeXt settings file via
`Preferences: simple_ConTeXt Settings` in the command palette or
`Preferences ▶ Package Settings ▶ simple_ConTeXt ▶ Settings` from the menu bar.
Under the `program_locations.ConTeXt_paths` key, put in a key-value entry for
the ConTeXt installation on your machine: the key is just a convenient name for
that installation, and the value should be the path to the `context` binaries.
For example: if you have the `context` program located at
`/some-path/context/tex/texmf-linux-64/bin/context` (so the ConTeXt installation
tree's root is at `/some-path/context/`), then you should write something like

```json
{
  "program_locations.ConTeXt_paths": {
    "example": "/home/user-name/.local/context/tex/texmf-linux-64/bin"
  }
}
```

If you have multiple versions of ConTeXt installed (e.g. a couple different TeX
Live versions and the ConTeXt Standalone) then you can put a name-path entry for
each one, and they can happily coexist.

Now when you go to build a ConTeXt file, the builder looks up what version of
ConTeXt you want by consulting the current value of the setting `current.path`,
which should be the name of a key in the `program_locations.ConTeXt_paths`
dictionary (so `example` as above). To quickly change between different versions
of ConTeXt, you can use the [Quick Settings](#quick-settings) command.

There are also some options to control how the builder functions and what output
to report.

### PDFs

For opening PDFs after building a ConTeXt file the `current.PDF/viewer` entry is
consulted. It should be the name of one of the keys in
`program_locations.PDF_viewers`.

Similarly to the previous, the keys in `program_locations.PDF_viewers` can be
any string, but each value should be the name of a PDF viewer program. (In the
case of Sumatra PDF viewer, this could be simply `sumatraPDF` if it's on your
environment path, or else an explicit path like `/usr/bin/sumatraPDF`.)

### Auto-Completion

Add the following entry to your general ST settings, in order to get automatic
completions for ConTeXt commands on typing the initial backslash <kbd>\\</kbd>.

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
    "active_selectors": ["definition", "file_name", "heading", "reference"],
    "selected_index": "closest"
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

Consider adding the following to your ConTeXt syntax specific settings. (You can
access these via `Preferences: Settings - Syntax Specific` in the command
palette or `Preferences ▶ Settings - Syntax Specific` from the menu bar, as long
as the currently active view has the ConTeXt syntax.)

```json
{
  "spell_check": true,
  "spelling_selector":
    "text.tex.context - (meta.control-word.context, meta.environment.math.context, meta.brackets.context, source, markup.raw, comment)"
}
```

This should do a pretty decent job at limiting spell check to the appropriate
places only (e.g. not in maths or code blocks).

### Bracket Highlighter

If you use the excellent [BracketHighlighter][bracket-highlighter] package, then
adding the following to the BracketHighlighter settings will provide some
support for ConTeXt start/stop commands.

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
      "plugin_library":
        "simple_ConTeXt.bracket_highlighter.context_environments",
      "enabled": true
    }
  ]
}
```

The file `context_environments.py` pointed to here under the `plugin_library`
key simply checks that the start and stop tags match.

## Builders

The main builder is of course the ConTeXt one, that is a wrapper around the
`context` binary. In order to find `context` it consults the path specified in
the settings.

As it's relatively easy to do so, there are a couple other builders:

- Lua (using LuaTeX as a Lua interpreter);
- MetaPost. There are two variants: firstly, just use the version of `mpost`
  that ships with the ConTeXt installation. Alternatively, use `context` itself:
  when called on a MetaPost file, it will compile it (using the MetaFun format)
  into a PDF.

Both of these rely on the setting `current.path` to find the relevant programs.

## Snippets

There are various snippets for ConTeXt (and a couple for MetaPost as well). You
can find these by typing `snippet` in the command palette in a ConTeXt file, but
here is a quick summary.

- Samples, analogous to the built-in snippet `lorem`. These are: `bryson`,
  `carey`, `carrol`, `darwin`, `davis`, `dawkins`, `douglas`, `greenfield`,
  `hawking`, `jojomayer`, `khatt`, `klein`, `knuth`, `linden`, `montgomery`,
  `reich`, `sapolsky`, `thuan`, `tufte`, `waltham`, `ward`, `weisman`, and
  `zapf`.
- Headings, for part/chapter/section and so on: `chap`, `part`, `title`, `sec`,
  `sub`, `sec2`, `sub2`, `sec3` and `sub3`.
- For item groups: `items` and `item`
- For mark-up: `bf`, `em`, `emph`, `it`, and `sl`.
- For tables: `tabn`, `tabln`, `tabu`, and `tabx`.
- For math: `align`, `form`, `forma`, `pform`, `pforma`, and `math`.
- For Lua: `lua`, `ctx`, and `lmx`.
- For projects/modules: `mod`, `comp`, `env`, and `prod`.
- For placing things: `place`,  `pfig`, and `ptab`.
- Others: `start`, `text`, `doc`, and `page`.

## Key/Value Auto-Complete

We added an auto-completion feature, can be turned on or off with the option
`current.option_completions/on`. For an example, suppose you typed
`\setuphead[c`. Then (provided you had this option turned on) you would see a
list of suggested options pop up: at time of writing I am suggested the options
`catcodes`, `color`, `command`, `commandafter`, `commandbefore`, `continue`,
`conversion`, and `coupling`. (These are provided by a simple idea: given a
command `\foo`, suggest any keys from key-value options that `\foo` has itself,
in addition to (in a recursive manner) any keys from key-value commands that
`\foo` inherits.)

## Quick Settings

In the command palette there is a command called
`simple_ConTeXt: Quick change the settings`. It brings up an interactive menu
for browsing and modifying the current settings. Some things (e.g. adding new
settings) need to be done by opening up the settings the traditional ST way, but
especially for modifying existing options this command can be a nice time saver.

## Scripts

We provide a command `simple_ConTeXt: Run a ConTeXt script` in the ST palette.
It is a straightforward wrapper around a command line, with the environment path
modified to include the path to the ConTeXt binaries currently chosen in the
settings (the one named `current.path`). It also expands the default ST
variables (e.g. `$file`). (Note that it is very basic at the moment, it simply
waits for the script to finish and only then reports the result. Also, if the
script has an error of some kind then this command can get stuck; in this way it
is quite fragile currently.)

This can be a convenience if you have multiple installations of ConTeXt on one
machine, as it takes care of setting up your `PATH` for you. Then you can do
things like

```shell
mtxrun --generate --force
```

to (re)generate the file database for the version of ConTeXt currently active in
simple ConTeXt (typically takes a few seconds), and

```shell
mtxrun --script font --list --pattern=*latinmodern* --all
```

to look up all the Latin Modern fonts that ConTeXt is aware of.

## Misc

Completions should play well with others, e.g. the completions provided by the
[UnicodeCompletion][unicode-completion] package. (Although UnicodeCompletion is
intended for LaTeX, I still find it useful for ConTeXt as many of the command
names are the same.)

## Future Features

A couple of features that I think would be nice to have. Of course, we can go
and on imagining things to add/improve.

- Extend the `key=val` auto-completion stuff to include value suggestions.
- Add support for multi file documents. This is not something I do very much,
  so I'm not sure what it should look like. Have the builder figure out the
  master file? What other things would be useful?
- Add support for the syntax `\start[foo] ... \stop` as a valid alternative to
  `\startfoo ... \stopfoo`. Again, not something I use, is this a sensible idea?
- Add option for return focus to ST after opening PDF on build.
- SyncTeX support. (Forward and backward jump to PDF.) What's the situation
  with SyncTeX in ConTeXt?
- Code formatter.
- Extend the command auto-complete/pop-up system to allow for user-defined
  commands. Easiest would probably be to define them in the `.xml` style that
  the ConTeXt interface files use.
- Fix up the documentation browser. I saw some discussion on the mailing list
  about using commands like `mtxrun --launch cld-mkiv.pdf` to open the docs,
  which would be nice for this.
- Checker/linter. (The checks provided by `mtxrun --script check` are quite
  basic, last I 'checked'. I don't know that `chktex` has much ConTeXt support,
  seems to be targeted at LaTeX.)
- Robust log parsing, esp. for reporting warnings/errors. Related to this, put
  phantom errors back in.
- Word count. (Could be nice to have, but lots of difficulties with it.)
- Handle `\unprotect ... \protect` in a nice way.

[context-introduction]: http://wiki.contextgarden.net/What_is_ConTeXt
[package-control]:      https://packagecontrol.io
[sublime-text]:         https://www.sublimetext.com
[unicode-completion]:   https://github.com/randy3k/UnicodeCompletion
[bracket-highlighter]:  https://github.com/facelessuser/BracketHighlighter
[package-dev]:          https://github.com/SublimeText/PackageDev
