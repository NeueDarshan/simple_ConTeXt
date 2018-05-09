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
  - [Interface Files](#interface-files)
- [References](#references)
- [Citations](#citations)
- [File Links](#file-links)
- [Commands](#commands)
  - [Auto-Complete](#auto-complete)
  - [Pop-Ups](#pop-ups)
- [Builders](#builders)
  - [Normal Builders](#normal-builders)
  - [Build on Save](#build-on-save)
- [Key/Value Auto-Complete](#keyvalue-auto-complete)
- [Settings](#settings)
  - [Quick Settings](#quick-settings)
  - [Manual](#manual)
- [Scripts](#scripts)
- [Snippets](#snippets)
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
- Handling of references.
- Handling of citations.
- Various snippets.
- Other miscellany.

(I should say that I use ConTeXt MkIV exclusively, and so the package is
designed and tested with MkIV only. In other words, if MkII stuff works then it
is a happy accident. That said, the syntax file should work perfectly well for
MkII, and I would guess that most of the other parts should be relatively
simple to adapt as needed.

Also, the multilingual interface in ConTeXt is not something I have considered.
I only know the English interface, and have worked with it in mind; the task of
supporting all of the different interfaces simultaneously seems rather daunting
to me!)

## Installation/Setup

Install via [package control][package-control], under the name `simple_ConTeXt`.
(Alternatively, you can just `git clone` the repository into your Sublime Text
(ST) packages directory.) Afterwards, there are some optional things to set up.

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
  "args": {"selected_index": "closest"},
  "context": [
    {
      "key": "selector",
      "operator": "equal",
      "operand": "text.tex.context"
    }
  ]
}
```

Otherwise, the default local symbol list contains all these things and uses prefixes to distinguish between e.g. headings and definitions.

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

### Interface Files

TODO: talk some about them.

## References

We support references, as powered by the ConTeXt syntax file. (So we know what
things are references because the syntax file has rules that tell us so.
Although many common cases are taken care of, I think there are still some that
are not.) To quickly illustrate the idea, suppose you had the document

```tex
\starttext
  \startplaceformula[reference={eq:pythag}]
    \startformula
      a^2 + b^2 = c^2
    \stopformula
  \stopplaceformula

  Lorem ipsum ...
\stoptext
```

If you were to type `\in{equation}[`, say, then a quick-panel would pop up
showing every reference in the file (just the one in this case, `eq:pythag`).
Selecting an entry will type it in automatically.

You can turn this functionality on or off completely with the setting
`current.references/on`. To add new reference commands (in addition to the
built-ins `\in` and friends) into the system (e.g. `\eqref`) there is the option
`current.references/command_regex`.

## Citations

We provide some support for citations, in the new MkIV style. (For reference,
see the manual 'Bibliographies: The ConTeXt Way' (a.k.a.
`mkiv-publications.pdf`)). We can parse bibliographic databases in the
traditional BibTeX format, as well as in the Lua and XML formats. As a quick
intro/example, suppose the file `example.bib` looks like

```
@book{foo-bar,
  title  = "Foo Bar",
  author = "A. U. Thor",
}
```

and in the same directory we have a file as follows.

```tex
\usebtxdataset[example.bib]
\starttext
  Lorem ipsum dolor sit amet, ...
\stoptext
```

If we type `\cite[` somewhere in this document, then a quick-panel will pop up
listing every entry in `example.bib`, so in this case just the single book 'Foo
Bar'. Selecting an entry from the list will then input the tag associated to
that entry.

This functionality can be turned on or off with the setting
`current.citations/on`. To control what information we show in the quick-panel,
there is the setting `current.citations/format`. It's default value is the
string

```
{title}<>{author}<>{category}, {year}, {tag}
```

The braces `{...}` indicate a bibliographic field name, and the sequence `<>`
indicates the start of a new row.

To demonstrate the other formats, here is what the equivalent `example.lua`
might look like:

```lua
return {
  ["foo-bar"] = {
    category = "book",
    title    = "Foo Bar",
    author   = "A. U. Thor",
  }
}
```

Finally, compare the same data in XML format.

```xml
<bibtex>
  <entry tag="foo-bar" category="book">
    <field name="title">Foo Bar</field>
    <field name="author">A. U. Thor</field>
  </entry>
</bibtex>
```

## File Links

Some commands involve another file (e.g. `\input`), and for some of these we can
show a hyperlink to that file. For example, consider the document

```tex
\environment example-style
\usebtxdataset[samples.bib]
\starttext
  \input knuth
\stoptext
```

Hovering over `example-style`, `samples.bib`, or `knuth` will do this.

As for what the link points to: we try to find the file in and around a given
documents location in the file tree (more precisely: we look in the directory
it's located at, as well as all sub-directories and it's parent directory), and
if that fails we ask `context` (well, `mtxrun`) if it knows where that file is
on the TeX tree. While doing this we consider typical extensions, so for example
when looking for `knuth` we also look for a `knuth.tex`.

You can turn this feature on or off with the setting `current.file_links/on`.

## Commands

### Auto-Complete

Provided you tell ST to do so as in [this section][#auto-completion], when
typing a backslash <kbd>\\</kbd> there will appear a list of all known command
names, as well as an indicator of how many arguments each command takes.

### Pop-Ups

When you type in a full command name, e.g. `\setupfittingpage`, or if you hover
over a full command name, a pop-up will appear. They look something like this:

<!-- This doesn't come out right on Package Control, not sure what to do about
     that. -->

```tex
                      1           2
\setupfittingpage [...,...] [..,..=..,..]
                     OPT

1   NAME

2   command = \...#1
    margin = page
    pagestate = start stop
    paper = auto default NAME
    scale = NUMBER
    inherits: \setupframed

page-app.mkiv
```

The formatting should be fairly self-explanatory. A couple of notes:

- The `OPT` here is short for 'optional argument'.
- Default values are indicated by underlines (not shown here).
- Upper-case values (e.g. `NUMBER`) indicate you can pass a value of that type
  (a 'number').
- Values like `\...#1#2` indicate you can pass a command `\foo` which expects
  some number of arguments.
- Sometimes there is a value `inherits: \...`, which indicates that this option
  inherits the options of that command.
- At the end there can be a hyperlink to a file name (`page-app.mkiv` here)
  where the command is defined.

There are a few options in the settings to tweak their appearance, and you can
toggle whether they are shown at all by typing/hovering with the settings
`current.pop_ups/methods/on_modified` and `current.pop_ups/methods/on_hover`
respectively.

## Builders

### Normal Builders

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

### Build on Save

There is an auto-build functionality: I'm not sure how useful it is, you can try
it out if you like. You can turn it on by setting `current.builder/auto/on` to
`true`. Then, whenever you save a ConTeXt file (i.e. a view in ST that has the
'ConTeXt' syntax) we run the ConTeXt builder.

There a couple of options related to this, all starting with the string
`current.builder/auto/`. Of particular interest is
`current.builder/auto/extra_opts_for_ConTeXt`, which you can use to pass along
different options to the `context` process from the manual builder. The use-case
I imagine is: suppose you have some slow-to-build graphics that you would like
to skip while drafting a document. Then you can set

```json
{
  "current.builder/auto/extra_opts_for_ConTeXt": {
    "mode": {
      "draft": true
    }
  }
}
```

and in the document use commands like `\doifmodeelse` to conditionally execute
certain code:

```tex
\doifmodeelse {draft}
  {slow branch ...}
  {quick branch ...}
```

(Currently we just pass along any extra options on top of the default options;
maybe we should look at merging them instead.)

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

## Settings

### Quick Settings

In the command palette there is a command called
`simple_ConTeXt: Quick change the settings`. It brings up an interactive menu
for browsing and modifying the current settings. Some things (e.g. adding new
settings) need to be done by opening up the settings the traditional ST way, but
especially for modifying existing options this command can be a nice time saver.

### Manual

If you do need to manually edit the settings, then you can do so via
`Preferences: simple_ConTeXt Settings` in the command palette or
`Preferences ▶ Package Settings ▶ simple_ConTeXt ▶ Settings` from the menu bar.
All the options have some documentation in the default settings file.

Care has been taken to play nice with the autocomplete/pop-up functionality from
the great [Package Dev][package-dev] package.

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

```sh
mtxrun --generate --force
```

to (re)generate the file database for the version of ConTeXt currently active in
simple ConTeXt (typically takes a few seconds), and

```sh
mtxrun --script font --list --pattern=*latinmodern* --all
```

to look up all the Latin Modern fonts that ConTeXt is aware of.

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

## Misc

Completions should play well with others, e.g. the completions provided by the
[UnicodeCompletion][unicode-completion] package. (Although UnicodeCompletion is
intended for LaTeX, I still find it useful for ConTeXt as many of the command
names are the same.)

## Future Features

A couple of features that I think would be nice to have. Of course, we can go
and on imagining things to add/improve.

- Work on the interface generator, I think there is some simplifying we can do.
- Extend the `key=val` auto-completion stuff to include value suggestions.
- Add support for multi file documents. This is not something I do very much,
  so I'm not sure what it should look like. Have the builder figure out the
  master file? What other things would be useful?
- Add support for the syntax `\start[foo] ... \stop` as a valid alternative to
  `\startfoo ... \stopfoo`. Again, not something I use, is this a sensible idea?
- Implement option for return focus to ST after opening PDF on build.
- SyncTeX support. (Forward and backward jump to PDF.) What's the situation
  with SyncTeX in ConTeXt?
- Code formatter. (The ST syntax engine already does the hard work of parsing
  ConTeXt files, in quite some detail. This should make it relatively easy to do
  some basic auto-formatting. I'd want to be as non-invasive as possible, only
  formatting what we are certain it makes sense to do so.)
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
  phantom error functionality back in.
- Word count. (Can be nice to have, but very tricky in full generality.)
- Handle `\unprotect ... \protect` in a nice way.

[context-introduction]: http://wiki.contextgarden.net/What_is_ConTeXt
[package-control]:      https://packagecontrol.io
[sublime-text]:         https://www.sublimetext.com
[unicode-completion]:   https://github.com/randy3k/UnicodeCompletion
[bracket-highlighter]:  https://github.com/facelessuser/BracketHighlighter
[package-dev]:          https://github.com/SublimeText/PackageDev
