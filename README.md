# Contents

  - [Introduction](#introduction)
  - [Snippets](#snippets)
  - [Commands](#commands)
    - [Completions](#completions)
    - [Pop-Ups](#pop-ups)
  - [References](#references)
  - [Builder](#builder)
  - [Settings and Profiles](#settings-and-profiles)

# Introduction

This plugin aims to provide some support for working with the [ConTeXt][contextgarden] program. In particular, it provides:

  - syntax files to markup ConTeXt source files (and related files),
  - a couple of snippets for common use cases,
  - auto-completion for the roughly 4000 "core" ConTeXt commands,
  - pop-ups showing basic documentation on each of those commands,
  - a basic reference handling system,
  - a basic builder,
  - a "profile" system, mainly intended for managing multiple versions of ConTeXt on the same machine,
  - some settings to control these features.

More details on these features in their respective sections.

# Snippets

The snippets are as follows.

| snippet    | expands to                                   | notes                |
|------------|----------------------------------------------|----------------------|
| `lua`      | `\startluacode ... \stopluacode`             |                      |
| `template` | `<?lua ... ?>`                               | for "mkxi" templates |
| `math`     | `\startformula ... \stopformula`             |                      |
| `align`    | `\startalign ... \stopalign`                 |                      |
| `start`    | `\start<environment> ... \stop<environment>` |                      |
| `table`    | `\bTABLE ... \eTABLE`                        | shows example usage  |
| `TABLE`    | `\startTABLE ... \stopTABLE`                 | shows example usage  |
| `xtable`   | `\startxtable ... \stopxtable`               | shows example usage  |

They work anywhere in a ConTeXt file, except for `align` which only works inside math-mode.

# Commands

We use the name "commands" to refer to TeX/ConTeXt macros, such as `\starttext`. We also speak of "core" commands, i.e. those commands defined in the interface XML files ConTeXt generates.

There are two quality of life features we provide for core commands, "completions" and "pop-ups".

## Completions

Completions will suggest possible commands from the ConTeXt core whenever you start typing a command.

For example, on typing `\TABLE` a drop-down list appears, showing those commands that match the string `"TABLE"` (according to the "fuzzy search" in Sublime Text). It should look something like this (in this case there are a lot of commands matching `"TABLE"`, so we just show the first few entries):

    \TaBlE
    \TABLE
    \bTABLE
    \eTABLE
    \bTABLEbody
    \bTABLEfoot
    ...

These can be turned on or off by setting the `command_popups/on` key in the settings to `true` or `false`.

## Pop-Ups

Pop-ups go hand-in-hand with the completions feature. On typing in the full name of a command from the ConTeXt core, a pop-up will display showing documentation for that command. (In some cases a command can be used in a couple of different ways; in such cases the pop-up will show a list of all the different options.)

These are created automatically using the XML interface files that ConTeXt generates, and only provide basic information about each command; they do *not* describe in words what the command is for or how to use it. Nevertheless they can be quite useful. For example, `\startTABLE` has the pop-up

                      1
    \startTABLE [..,..=..,..] ... \stopTABLE
                     OPT

    1   inherits: \setupTABLE

    tabl-ntb.mkiv

This indicates that `\startTABLE` takes one optional argument, which is a list of key-value assignments (so for example, something like `[color=red, style=bold]`), and that the recognized options are the same as those in the command `\setupTABLE`. Furthermore, it shows that `\startTABLE` should be terminated with a matching `\stopTABLE`. The line `tabl-ntb.mkiv` indicates the original file where this command is defined, and can be turned on or off by setting the `command_popups/show_files` key to `true` or `false` in the settings.

# References

References are tricky. There are two main jobs we try to automate when handling references,

  - keeping track of the "labels" defined so far, things like `[eq:pythagoras]`,
  - automatically prompting the user to choose a label when they type certain commands, e.g. after typing `\eqref`.

The current approach is to allow users to define a regex describing what their references look like (this can be set using the `references/reference_regex` key), and a regex to describe after which commands they want to choose a reference (corresponding to the `references/command_regex` key). In this way, for example, we can easily deal with extra "reference handlers" defined via `\definereferenceformat`.

To illustrate, the settings

    "references":
    {
      "reference_regex": "[a-zA-Z]+:[a-zA-Z]+",
      "command_regex": "[a-zA-Z]*ref"
    }

mean that references such as `[part:introduction]` and `[reference=figure:main]` will be tracked correctly, and that typing something like `\partref` will bring up the list of references.

# Builder

We currently provide a very basic builder for ConTeXt files. It uses the `context_program/path` key (if given) to locate the ConTeXt program, and calls it (using the options in `context_program/options`, if any) on the current ConTeXt file.

Although the builder is a work in progress, it *does* currently handle settings in a nice way. That is, the `context_program/options` key offers quite some, well, options. You can assign a string to it such as `--once --synctex` and this will get passed along to the program as if on the command line. Alternatively, you can use key-value pairs as in

    "options":
    {
      "synctex": false,
      "jit": true,
      "randomseed": 42,
      "runs": 1
    }

In this case, the ConTeXt program will receive the options `--jit --randomseed=42 --runs=1`. A key with boolean value will pass (or not) the option `--<key>` depending on if the value is `true` or `false`. A number of string as value will get passed as `--<key>=<value>`, and similarly for lists.

Bear in mind that some options *might* cannibalize each other, for example passing `--directives=<list>` and `--synctex` to ConTeXt *may* result in the `directives` being ignored.

# Settings and Profiles

We aim to provide a reasonable amount of flexibility in the settings. A basic setup could be something like:

    {
      "profiles":
      [
        {
          "name": "main profile",
          "command_popups":
          {
            "on": true
          },
          "context_program":
          {
            "path": "C:/path/to/context/program/"
          }
        },
        {
          "name": "other profile",
          "context_program":
          {
            "path": "D:/path/to/different/version/of/context/program/"
          }
        }
      ]
    }

Alternatively, you can use the `profile_defaults` key to assign settings common to *all* profiles, and then overwrite these settings where necessary on a profile by profile basis. For example:

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
          "path": "C:/path/to/context/program/"
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
        {
          "name": "other",
          "command_popups":
          {
            "on": false,
          }
        }
      ]
    }

Finally we provide an alternative inheritance model, via the `inherits` key. With this, you can fine-tune the hierarchy of profiles and cut down on repetition. Setting it to a string will try to inherit the profile settings going by that name (the name `profile_defaults` is taken to mean, use the settings in `profile_defaults`). Alternatively, setting it to a list will inherit the settings one by one, going from left-to-right in the list. Thus

    {
      "name": "test",
      "inherits": ["profile_defaults", "main", "other"],
      "context_program":
      {
        "path": "C:/path/to/context/program/"
      }
    }

will inherit the default options, overwrite them with the `main` options, overwrite them again with the `other` options, and finally overwrite these by the options explicitly given in this profile (i.e. set the `context_program/path` key to `"C:/path/to/context/program/"`).

[contextgarden]: http://wiki.contextgarden.net/What_is_ConTeXt
