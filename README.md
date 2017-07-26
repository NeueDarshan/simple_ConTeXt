# Contents

  - [Introduction](#introduction)
  - [Syntax](#syntax)
  - [Commands](#commands)
    - [Completions](#completions)
    - [Pop-Ups](#pop-ups)
  - [Snippets](#snippets)
  - [Symbols](#symbols)
  - [References](#references)
  - [Builder](#builder)
  - [Settings](#settings)

# Introduction

This [Sublime Text][sublimetext] package aims to provide some support for
working with the [ConTeXt][contextgarden] program. In particular, it provides:

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
commands we mean exactly those commands documented in the XML interface files
ConTeXt comes with.

To work with these XML files, we create our own JSON interface files
automatically from the XML files that a ConTeXt installation provides.
Different installations of ConTeXt may define slightly different commands, and
thus the XML files for each may differ. These are created automatically, by
tracking down the `i-context.xml` file in your ConTeXt installation.

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
Nevertheless they can be tremendously useful. For example, `\startTABLE` has
the pop-up

```TeX
                  1
\startTABLE [..,..=..,..] ... \stopTABLE
                 OPT

1   inherits: \setupTABLE

tabl-ntb.mkiv
```

This indicates that `\startTABLE` takes one optional argument, which is a list
of key-value assignments (so for example, something like `[color=red,
style=bold]`), and that the recognized options are the same as those of the
`\setupTABLE` command. Furthermore, it shows that `\startTABLE` should be
terminated with a matching `\stopTABLE`. The line `tabl-ntb.mkiv` indicates the
source file where this command is defined, if you're curious, and can be turned
on or off with the `settings/pop_ups/show_source_files` key. You can click on
it and it will open that file.

The colouring of the pop-ups is determined automatically based on the current
colour scheme. Pop-ups can be turned on or off completely with the
`settings/pop_ups/on` key.

The other keys in `settings/pop_ups` are `line_break` and `show_copy_pop_up`.

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

The current approach is a mix: on the one hand, when we can easily say for
definite that something is a reference then it is handled just fine. For the
other cases, there is a possibility to define a regex describing what the
references look like (this can be set using the
`settings/references/reference_regex` key), and a regex to describe after which
commands they want to choose a reference (corresponding to the
`settings/references/command_regex` key). In this way, for example, extra
"reference handlers" defined via `\definereferenceformat` can be dealt with.

To illustrate, the settings

```JSON
{
  "settings": {
    "references": {
      "reference_regex": "[a-zA-Z_\\.\\-\\:]*[_\\.\\-\\:]+[a-zA-Z_\\.\\-\\:]*",
      "command_regex": "(in|at|[a-zA-Z]*ref)"
    }
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

The main builder uses the `path` key (if given) to locate the main program, and
calls it (by default "context", can be set via `settings/builder/program/name`)
(passing the options in `settings/builder/program/options`, if any) on the
current ConTeXt file. It is invoked in the standard way
(<kbd>Ctrl</kbd>+<kbd>B</kbd>) and can be cancelled part-way through by
"running" it again.

There is also a variant of this builder (you can see both by pressing
<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd>), which calls
`mtxrun --script check ...`, i.e. does a (basic) syntax check instead.

Note: the `path` option can be used either as an explicit path, or instead the
name of a path in `paths`. The second alternative could look like:

```JSON
{
  "paths": {
    "default": "/path-to-context-binaries",
  },
  "settings": {
    "path": "default"
  }
}
```

The value of `settings/builder/program/options` offers quite some, well,
options. You can simply assign a string to it such as `--once --synctex` and
this will get passed along to the program as if on the command line. Better is
to use key-value pairs as in (for example)

```JSON
{
  "settings": {
    "builder": {
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
information to report or not, namely the booleans:

  - `show_errors_in_builder`
  - `show_errors_in_main_view`
  - `show_full_command_in_builder`
  - `show_pages_shipped_in_builder`
  - `show_path_in_builder`
  - `show_warnings_in_builder`

Also there is `settings/builder/PDF` which contains the settings `PDF_viewer`
(a string for the name of a PDF viewer that is on your `PATH`) and
`auto_open_PDF`, a boolean.

Finally, there are the settings

  - `check_syntax_before_build`
  - `stop_build_if_check_fails`

in `settings/builder/check`. They control whether to do a syntax check before
running ConTeXt, and if so, whether to stop on a negative result of the
checker.

# Settings

In the command palette there is a command "simple_ConTeXt: View/change the
settings", which opens a little GUI for handling the settings. It has some
limitations, but it is pretty flexible and is usually quicker to change one
setting than editing the actual settings file.

Of course the settings are in fact just a JSON file (well, technically a
`sublime-settings` file which is slightly different). An example of such a
settings file could be:

```JSON
{
  "paths": {
    "default": "...",
  },
  "setting_schemes": {
    "verbose_builder_off": {
      "builder": {
        "show_errors_in_builder": false,
        "show_full_command_in_builder": false,
        "show_pages_shipped_in_builder": false,
        "show_path_in_builder": false,
        "show_warnings_in_builder": false
      }
    },
    "verbose_builder_on": {
      "builder": {
        "show_errors_in_builder": true,
        "show_full_command_in_builder": true,
        "show_pages_shipped_in_builder": true,
        "show_path_in_builder": true,
        "show_warnings_in_builder": true
      }
    }
  },
  "settings": {
    "builder": {
      "program": {
        "options": {
          "autogenerate": true,
          "synctex": "zipped"
        },
        "path": "default"
      }
    },
    "pop_ups": {
      "on": true,
      "line_break": 65,
    },
    "references": {
      "on": true,
      "command_regex": "(in|at|about|[a-zA-Z]*ref)",
      "reference_regex": "[a-zA-Z_\\.\\-\\:]+"
    }
  }
}
```

There is `setting_schemes` option in the settings which can be used to group
together settings. For example, `verbose_builder_off` and `verbose_builder_on`
in the above example. These do nothing in and of themselves, but the GUI is
aware of them: in it you can select one of them, and this applies all the
settings contained within. Another use case might be switching between
installations of ConTeXt:

```JSON
{
  "setting_schemes": {
    "set_alpha": {
      "path": "alpha"
    },
    "set_beta": {
      "path": "beta"
    }
  },
  "paths": {
    "alpha": "/path-to-alpha-binaries",
    "beta": "/path-to-beta-binaries"
  }
}
```

This has become simpler in more recent versions of this package to the point
where it's hardly worth doing it this way, if the only thing you change is the
`path`. Instead you can just open up the command palette, choose
"simple_ConTeXt: View/change the settings", and select "path" there to choose
between, say, "alpha" and "beta".

[sublimetext]: https://www.sublimetext.com
[contextgarden]: http://wiki.contextgarden.net/What_is_ConTeXt
[titles]: http://wiki.contextgarden.net/Titles
[metapost]: http://wiki.contextgarden.net/MetaPost
[metafun]: http://wiki.contextgarden.net/MetaFun
