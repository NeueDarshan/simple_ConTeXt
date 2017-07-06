# Contents

  - [Introduction](#introduction)
  - [Syntax](#syntax)
  - [Commands](#commands)
    - [Completions](#completions)
    - [Pop-Ups](#pop-ups)
    - [Generating an Interface](#generating-an-interface)
  - [Snippets](#snippets)
  - [Symbols](#symbols)
  - [References](#references)
  - [Builder](#builder)
  - [Settings](#settings)

# Introduction

This plugin aims to provide some support for working with the
[ConTeXt][contextgarden] program. In particular, it provides:

  - syntax files to markup ConTeXt source (and related) files,
  - auto-completion for the user-facing ConTeXt commands,
  - pop-ups showing some documentation on each of those commands,
  - a builder,
  - a reference system,
  - a GUI for managing the settings,

and other bits and pieces. More details on these features in their respective
sections. Note that ConTeXt MKIV is supported, but not older versions (i.e.
MKII): in this README "ConTeXt" means the MKIV version.

# Syntax

There are a couple of `sublime-syntax` files provided related to using ConTeXt.

  - "ConTeXt" is the main one, which handles ConTeXt source files (typically
    `.tex` or `.mkiv`)
  - "ConTeXt Log" handles the log files that the ConTeXt program generates.
  - "MetaPost" is for the [graphic programming language][metapost].
  - "MetaFun" is for the [macro-package][metafun] extension to the MetaPost
    language, which is loaded by default when using MetaPost within ConTeXt.

# Commands

By "commands" we mean TeX/ConTeXt macros, such as `\starttext`. By "core"
commands we mean those commands defined in the XML interface files ConTeXt
comes with. There are three features implemented for core commands: "browsing",
"completions" and "pop-ups".

## Browsing

This is just a quick example feature making use of the interface JSON files. In
the command palette (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>) there is a
command called "simpleConTeXt: Browse interface commands"; you can choose an
interface (provided one has already been created, see the
[interface](#generating-an-interface) section) and then peruse the library of
core commands at your leisure.

You can do the same kind of thing with completions, but this provides a nicer
interface for it. It is pretty basic currently.

## Completions

Completions suggest possible commands from the ConTeXt core whenever you start
typing a command.

For example, on typing `\TABLE` a drop-down list appears, showing those
commands that match the string "TABLE" (according to the fuzzy search in
Sublime Text). It should look something like this (in this case there are a lot
of commands matching "TABLE", so only the first few entries are shown):

```TeX
\TaBlE
\TABLE
\bTABLE
\eTABLE
\bTABLEbody
\bTABLEfoot
...
```

## Pop-Ups

Pop-ups go hand-in-hand with completions. On typing in the full name of a core
command, a pop-up will appear showing the documentation for that command. (In
some cases a command can be used in a couple of different ways; in such cases
the pop-up will show a list of all the different options.)

These are created automatically using the XML interface files that ConTeXt
generates, and only provide basic information about each command; they do *not*
describe in plain English what the command is for or how to use it.
Nevertheless they can be quite useful. For example, `\startTABLE` has the
pop-up

```TeX
                  1
\startTABLE [..,..=..,..] ... \stopTABLE
                 OPT

1   inherits: \setupTABLE

tabl-ntb.mkiv
```

This indicates that `\startTABLE` takes one optional argument, which is a list
of key-value assignments (so for example, something like
`[color=red, style=bold]`), and that the recognized options are the same as
those of the `\setupTABLE` command. Furthermore, it shows that `\startTABLE`
should be terminated with a matching `\stopTABLE`. The line `tabl-ntb.mkiv`
indicates the source file where this command is defined, if you're curious, and
can be turned on or off with the `settings/pop_ups/show_files` key.

The colouring of the pop-ups is determined by the name in the
`settings/pop_ups/colour_scheme` key. (The values in the colour schemes are
used for CSS styling of the HTML-based pop-ups, so any valid way of specifying
a colour in CSS works. Thus `red`, `rgb(255, 0, 0)` and `#ff0000` are all
valid.) For example, the options

```JSON
"settings": {
  "pop_ups": {
    "colour_scheme": "test"
  }
}
```

and

```JSON
"colour_schemes": {
  "test": {
    "background": "rgb(222, 217, 200)",
    "primary": "rgb(39, 139, 210)",
    "secondary": "rgb(101, 123, 131)"
  }
}
```

complement "Boxy Solarized Light" version of [Boxy][boxy-sol].

Pop-ups can be turned on or off completely with the `settings/pop_ups/on` key,
and `settings/pop_ups/interface` can be used to specify which version of the
ConTeXt interface files to use (as different versions of ConTeXt can have
different interfaces).

The other keys in `settings/pop_ups` are `line_break`, `sort_keys` and
`sort_lists`.

## Generating an Interface

All the [command](#commands) features rely on so-called "interface" files.
These are simply JSON files, created automatically from the XML files that a
ConTeXt installation provides. Different installations of ConTeXt will define
different commands, and thus the XML files for each will differ. So there is
the `interfaces` key, which should contain key-value pairs something like the
following:

```JSON
"interfaces": {
  "example": {
    "main": "/path-to-tex-tree/texmf-context/tex/context/interface/mkiv",
    "modules": "/path-to-tex-tree/texmf-modules/tex/context/interface/third"
  }
}
```

"Main" should point to the main XML files (they are named in the scheme
`i-<name>.xml`). Optionally you can locate the module XML files, and then
simpleConTeXt will be able to understand the commands defined in the ConTeXt
modules. (Well, some of them, not all of them have associated XML files. And
some of the XML files might be malformed.)

Then you should bring up the command palette
(<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>) and select "simpleConTeXt:
Generate profile interface", and select the interface you just configured in
the settings file. Any errors will be reported in the console. Assuming it was
successful, the other features should now work. (Remember to also choose that
"interface" if necessary.)

# Snippets

The main snippets are as follows.

| snippet  | expansion                                    | notes               |
|----------|----------------------------------------------|---------------------|
| lua      | `\ctxlua{...}`                               |                     |
| luacode  | `\startluacode ... \stopluacode`             |                     |
| template | `<?lua ... ?>`                               | for mkxi templates  |
| math     | `\math{ ... }`                               | text-mode only      |
| formula  | `\startformula ... \stopformula`             | text-mode only      |
| align    | `\startalign ... \stopalign`                 | math-mode only      |
| em       | `{\em ... }`                                 | text-mode only      |
| bf       | `{\bf ... }`                                 | text-mode only      |
| start    | `\start<environment> ... \stop<environment>` |                     |
| table    | `\bTABLE ... \eTABLE`                        | shows example usage |
| TABLE    | `\startTABLE ... \stopTABLE`                 | shows example usage |
| xtable   | `\startxtable ... \stopxtable`               | shows example usage |

Additionally, there are the following snippets (which are taken from the
ConTeXt samples) which are analogous to the `lorem` snippet that comes "out of
the box" in Sublime Text:

`aesop`, `bryson`, `carey`, `cervantes`, `darwin`, `davis`, `dawkins`,
`douglas`, `hawking`, `khatt`, `knuth`, `linden`, `materie`, `montgomery`,
`quevedo`, `reich`, `thuan`, `tufte`, `waltham`, `ward`, `weisman`, `zapf`.

# Symbols

Using "Goto Symbol" (<kbd>Ctrl</kbd>+<kbd>R</kbd>) in Sublime Text will bring
up a list of "headings" you can navigate, i.e. chapters/sections/subsections
etc. See this [context garden article][titles] for details on ConTeXt headings.
Both the older style `\section{<name>}` and the newer style
`\startsection[title=<name>] ... \stopsection` are supported.

For example, in the document

```TeX
\starttext

\startpart[title=One]

\chapter{A}

\section{i}
\section{ii}

\chapter{B}

\chapter{C}

\stoppart

\stoptext
```

the list of symbols is

```
One
  A
    i
    ii
  B
  C
```

# References

References are tricky. There are two main tasks to handle:

  - keeping track of the "labels" defined so far, things like
    `[eq:pythagoras]`;
  - automatically prompting the user to choose a label when they type certain
    commands, e.g. after typing `\eqref`.

The current approach is to allow users to define a regex describing what their
references look like (this can be set using the
`settings/references/reference_regex` key), and a regex to describe after which
commands they want to choose a reference (corresponding to the
`settings/references/command_regex` key). In this way, for example, extra
"reference handlers" defined via `\definereferenceformat` can be dealt with.

To illustrate, the settings

```JSON
"settings": {
  "references": {
    "reference_regex": "[a-zA-Z]+:[a-zA-Z]+",
    "command_regex": "(in|at|[a-zA-Z]*ref)"
  }
}
```

mean that references such as `[part:introduction]` and `[figure:main]` will be
tracked correctly, and that typing something like `\partref` will bring up the
list of references.

Note that these strings (the values in `settings/references/reference_regex`
and `settings/references/command_regex`) are loaded in Python 3 via the `re`
module. So Python-style regular expressions are in order, and you may need to
escape certain characters e.g. a "-" character in a character class `[...]`.

# Builder

The builder uses the `settings/program/path` key (if given) to locate the main
program, and calls it (by default "context", can be set via
`settings/program/name`) (passing the options in `settings/program/options`, if
any) on the current ConTeXt file. It is invoked in the standard way
(<kbd>Ctrl</kbd>+<kbd>B</kbd>) and can be cancelled part-way through by running
it again.

Note: the `path` option can be used either as an explicit path, or instead the
name of a path in `program_paths`. The second alternative could look like:

```JSON
"program_paths": {
  "default": "/path/to/context/binaries",
},
"settings": {
  "program": {
    "path": "default"
  }
}
```

The value of `settings/program/options` offers quite some, well, options. You
can simply assign a string to it such as `--once --synctex` and this will get
passed along to the program as if on the command line. Better is to use
key-value pairs as in (for example)

```JSON
"settings": {
  "program": {
    "options": {
      "autogenerate": true,
      "runs": 3,
      "mode": {
        "draft": true
      },
      "synctex": "zipped"
    }
  }
}
```

In this example, the ConTeXt program will receive the options
`--autogenerate --runs=3 --mode=draft --synctex=zipped`. A key with boolean
value will pass (or not) the option `--<key>` depending on if the value is
`true` or `false`. A number or string as value will get passed as
`--<key>=<value>`. The "mode" option gets special treatment, and is passed as
`mode=<comma-separated-list>` including the "modes" that are set as `true`.

Bear in mind that some options *might* cannibalize each other, for example
passing `--directives=<some list>` and `--synctex` to ConTeXt can, in the
authors experience, result in the `directives` being ignored. Speculation: this
is due to the "synctex" flag being interpreted as
`--directives="system.synctex=1"` and therefore overwriting the previous
directives.

The builder takes a couple of options (in `settings/builder`) for what
information to report or not, namely the booleans `show_errors`, `show_pages`,
`show_path`, `show_full_command`, and `show_warnings`.

# Settings

In the command palette there is a command "simpleConTeXt: View/change the
settings", which manages a little GUI for handling the settings. It has some
limitations, but it is pretty flexible and is usually quicker to change one
setting than editing the actual settings file.

Of course the settings are in fact just a JSON file (well, technically a
`sublime-settings` file which is slightly different). An example of such a
settings file could be:

```JSON
{
  "colour_schemes": {},
  "interfaces": {
    "default": {
      "main": "...",
      "modules": "..."
    }
  },
  "program_paths": {
    "default": "...",
  },
  "setting_schemes": {
    "verbose_off": {
      "builder": {
        "show_errors": false,
        "show_pages": false,
        "show_path": false,
        "show_full_command": false,
        "show_warnings": false
      }
    },
    "verbose_on": {
      "builder": {
        "show_errors": true,
        "show_pages": true,
        "show_path": true,
        "show_full_command": true,
        "show_warnings": true
      }
    }
  },
  "settings": {
    "builder": {},
    "pop_ups": {
      "on": true,
      "interface": "default",
      "colour_scheme": "default",
      "line_break": 70,
    },
    "program": {
      "options": {
        "autogenerate": true,
        "synctex": "zipped"
      },
      "path": "default"
    },
    "references":
    {
      "on": true,
      "command_regex": "(in|at|about|[a-zA-Z]*ref)",
      "reference_regex": "[a-zA-Z_\\.\\-\\:]+"
    }
  }
}
```

There is `setting_schemes` option in the settings which can be used to group
together settings. For example, `verbose_off` and `verbose_on` in the above
example. These do nothing in and of themselves, but the GUI is aware of them:
in it you can select one of them, and this applies all the settings contained
within. Another use case might be switching between installations of ConTeXt:

```JSON
"setting_schemes": {
  "set_alpha": {
    "pop_ups": {
      "interface": "alpha"
    },
    "program": {
      "path": "alpha"
    }
  },
  "set_beta": {
    "pop_ups": {
      "interface": "beta"
    },
    "program": {
      "path": "beta"
    }
  }
}
```

with the relevant information put into `interfaces` and `program_paths` for
each.

[contextgarden]: https://wiki.contextgarden.net/What_is_ConTeXt
[titles]: https://wiki.contextgarden.net/Titles
[metapost]: https://www.tug.org/metapost.html
[metafun]: https://wiki.contextgarden.net/MetaFun
[boxy-sol]: https://github.com/ihodev/sublime-boxy#boxy-solarized-light--iowa
