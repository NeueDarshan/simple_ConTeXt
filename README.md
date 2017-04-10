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
  - [Settings and Profiles](#settings-and-profiles)

# Introduction

This plugin aims to provide some support for working with the
[ConTeXt][contextgarden] program. In particular, it provides:

  - syntax files to markup ConTeXt source files (and related files),
  - auto-completion for the roughly 4000 "core" ConTeXt commands,
  - pop-ups showing basic documentation on each of those commands,
  - a basic reference handling system,
  - a basic builder,
  - a "profile" system, mainly intended for managing multiple versions of
    ConTeXt on the same machine,

and other bits and pieces. More details on these features in their respective
sections. Note that ConTeXt MKIV is supported, and not older versions (i.e.
MKII): in this README "ConTeXt" means the MKIV version.

# Syntax

There are a couple of "sublime-syntax" files provided related to using ConTeXt.

  - "ConTeXt" is the main one, which handles ConTeXt source files, e.g. `.tex`
    and `.mkiv` files.
  - "ConTeXt Log" handles the log files that the ConTeXt program generates.
  - "MetaPost" is a [graphic programming language][metapost], a little rough
    around the edges currently.
  - "MetaFun" is a [macro-package][metafun] extension to the MetaPost language,
    and is loaded by default when using MetaPost within ConTeXt.

# Commands

"Commands" means TeX/ConTeXt macros, such as `\starttext`. "Core" commands
means those commands defined in the XML interface files ConTeXt generates.
There are three features so far for core commands: "browsing", "completions"
and "pop-ups".

## Browsing

This is just a quick example feature making use of the interface JSON files. In
the command palette (`Ctrl+Shift+P`) there is a command called "ConTeXtTools:
Browse interface commands"; you can choose an interface (provided one has
already been created, see the [interface](#generating-an-interface) section)
and then peruse the library of core commands at your leisure.

You can do the same kind of thing with completions, but this provides a nicer
interface for it.

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
can be turned on or off with the `command_popups/show_files` key.

The colouring of the pop-ups is determined by the `command_popups/colors` key.
(The values are used for CSS styling of the HTML-based pop-ups, so any valid
way of specifying a colour in CSS works. Thus `red`, `rgb(255, 0, 0)` and
`#ff0000` are all valid.) For example, the options

```JSON
"command_popups":
{
  "colors":
  {
    "background": "rgb(225, 225, 225)",
    "primary": "rgb(36, 151, 227)",
    "secondary": "rgb(86, 86, 86)"
  }
}
```

complement the "Light" version of [Monokai Extended][monokai].

Pop-ups can be turned on or off completely with the `command_popups/on` key,
and `command_popups/version` can be used to specify which version of the
ConTeXt interface files to use (as different versions of ConTeXt can have
different interfaces).

## Generating an Interface

All the [command](#commands) features rely on so-called "interface" files.
These are simply json files, created automatically from the XML files that a
ConTeXt installation provides. Different installations of ConTeXt will define
different commands, and thus the XML files for each will differ. So there is an
`interfaces` key at top-level in the settings, which should contain key-value
pairs like so:

```JSON
"interfaces":
{
  "one":
  {
    "main": "/path/to/main/interface",
    "modules": "/path/to/module/interface"
  }
}
```

"Main" should point to the main XML files (they are named in the scheme
`i-<name>.xml`), e.g. something like
`C:/texlive/2016/texmf-dist/tex/context/interface/mkiv` for a windows TeXLive
2016 installation. Optionally you can locate the module XML files, probably
right next the the main ones if they are anywhere (e.g. at
`C:\texlive\2016\texmf-dist\tex\context\interface\third`), and then
ConTeXtTools will also understand the commands defined in the ConTeXt modules.
(Well, some of them, not all of them have associated XML files.)

Then you should bring up the command palette (`Ctrl+Shift+P`) and select
"ConTeXtTools: Generate profile interface", and select the interface you just
configured in the settings file. Any errors will be reported in the console.
Assuming it was successful, the other features should now work. (Remember to
also switch to a profile using that "interface" if necessary.)

# Snippets

The snippets are as follows.

| snippet    | expands to                                   | notes                |
|------------|----------------------------------------------|----------------------|
| `lua`      | `\startluacode ... \stopluacode`             |                      |
| `template` | `<?lua ... ?>`                               | for "mkxi" templates |
| `math`     | `\startformula ... \stopformula`             |                      |
| `align`    | `\startmathalignment ... \stopmathalignment` |                      |
| `start`    | `\start<environment> ... \stop<environment>` |                      |
| `table`    | `\startTABLE ... \stopTABLE`                 | shows example usage  |
| `TABLE`    | `\bTABLE ... \eTABLE`                        | shows example usage  |
| `xtable`   | `\startxtable ... \stopxtable`               | shows example usage  |

They work anywhere in a ConTeXt file, except for `align` which only works
inside math-mode.

# Symbols

Using "Goto Symbol" (`Ctrl+R`) in Sublime Text will bring up a list of
"headings" you can navigate, i.e. chapters/sections/subsections etc. See this
[context garden article][titles] for details on ConTeXt headings. Both the
older style `\section{<name>}` and the newer style
`\startsection[title=<name>] ... \stopsection` are supported.

For example, in the file

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

the list of symbols looks like

```
One
  A
    i
    ii
  B
  C
```

# References

References are tricky. There are two main tasks to automate:

  - keeping track of the "labels" defined so far, things like
    `[eq:pythagoras]`;
  - automatically prompting the user to choose a label when they type certain
    commands, e.g. after typing `\eqref`.

The current approach is to allow users to define a regex describing what their
references look like (this can be set using the `references/reference_regex`
key), and a regex to describe after which commands they want to choose a
reference (corresponding to the `references/command_regex` key). In this way,
for example, extra "reference handlers" defined via `\definereferenceformat`
can be dealt with.

To illustrate, the settings

```JSON
"references":
{
  "reference_regex": "[a-zA-Z]+:[a-zA-Z]+",
  "command_regex": "(in|at|[a-zA-Z]*ref)"
}
```

mean that references such as `[part:introduction]` and `[figure:main]` will be
tracked correctly, and that typing something like `\partref` will bring up the
list of references.

Note that these strings (the values in `references/reference_regex` and
`references/command_regex`) are loaded in Python 3 via the `re` module. So
Python-style regular expressions are in order, and you may need to escape
certain characters e.g. a "-" character in a character class `[...]`.

# Builder

Currently the builder is pretty basic. It uses the `context_program/path` key
(if given) to locate the main program, and calls it (by default "context", can
be set via `context_program/name`) (passing the options in
`context_program/options`, if any) on the current ConTeXt file.

The value of `context_program/options` offers quite some, well, options. You
can assign a string to it such as `--once --synctex` and this will get passed
along to the program as if on the command line. Alternatively, you can use
key-value pairs as in

```JSON
"options":
{
  "autogenerate": true,
  "jit": true,
  "randomseed": 0.7,
  "runs": 1
}
```

In this example, the ConTeXt program will receive the options
`--autogenerate --jit --randomseed=0.7 --runs=1`. A key with boolean value will
pass (or not) the option `--<key>` depending on if the value is `true` or
`false`. A number or string as value will get passed as `--<key>=<value>`, and
similarly for lists.

Bear in mind that some options *might* cannibalize each other, for example
passing `--directives=<some list>` and `--synctex` to ConTeXt can result in the
`directives` being ignored. This is due to the "synctex" flag being interpreted
as `--directives="system.synctex=1"` and therefore overwriting the previous
directives.

# Settings and Profiles

The settings are intended to be flexible. A simple setup could be something
like this.

```JSON
{
  "profiles":
  [
    {
      "name": "main",
      "command_popups":
      {
        "on": true,
        "show_files": false,
        "interface": "context"
      },
      "context_program":
      {
        "path": "C:/path/to/context/program/",
        "options":
        {
          "autogenerate": true
        }
      }
    }
  ],
  "interfaces":
  {
    "context":
    {
      "main": "C:/path/to/interface/mkiv",
      "modules": "C:/path/to/interface/third"
    }
  }
}
```

Alternatively, you can use the `profile_defaults` key to assign settings common
to *all* profiles, and then overwrite these settings on a profile-by-profile
basis. For example (this time calling `mtxrun --script context ...` instead of
`context ...`):

```JSON
{
  "profile_defaults":
  {
    "command_popups":
    {
      "on": true,
      "show_files": false
    },
    "context_program":
    {
      "path": "~/path/to/context/program/",
      "name": "mtxrun",
      "options":
      {
        "script": "context"
      }
    }
  },
  "profiles":
  [
    {
      "name": "main"
    },
    {
      "name": "main (but only run once)",
      "context_program":
      {
        "options":
        {
          "runs": 1
        }
      }
    },
  ]
}
```

Finally there is an alternative inheritance model, via the `inherits` key. With
this, you can fine-tune the hierarchy of profiles and cut down on repetition.
Setting it to a string will try to inherit the profile settings going by that
name (the name `profile_defaults` is taken to mean, use the settings in
`profile_defaults`). More generally, setting it to a list will inherit the
settings one by one, going from left-to-right in the list. Thus

```JSON
{
  "name": "test",
  "inherits":
  [
    "profile_defaults",
    "main",
    "other"
  ],
  "context_program":
  {
    "path": "C:/path/to/context/program/"
  }
}
```

will inherit the default options, overwrite them with the `main` options,
overwrite them again with the `other` options, and finally overwrite these by
the options explicitly given in this profile (i.e. set the
`context_program/path` key to `"C:/path/to/context/program/"`).

[contextgarden]: http://wiki.contextgarden.net/What_is_ConTeXt
[titles]: http://wiki.contextgarden.net/Titles
[metapost]: http://www.tug.org/metapost.html
[metafun]: http://wiki.contextgarden.net/MetaFun
[monokai]: http://github.com/jonschlinkert/sublime-monokai-extended
