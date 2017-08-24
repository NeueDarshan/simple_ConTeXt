# Introduction

This [Sublime Text][sublimetext] package aims to provide some support for working with the [ConTeXt][contextgarden] program.

# Completions

Completions suggest possible commands whenever you start typing a command. For example the `\setuphead` command accepts many options, which are displayed as follows.

![example completions][completion]

They are unique to each `path`, i.e. to each ConTeXt installation configured in the settings. As such, they take a little while to set themselves up in the background the first time. Some details as to the progress of this set-up work is reported in the console.

## Pop-Ups

On typing in the full name of a command, a pop-up will appear showing the documentation for that command. For the same reason as the [completions](#completions), there is some first-time set-up work to be done.

Assuming all has gone well with the set-up, the pop-ups should look something like this:

![example pop-up][popup]

This particular pop-up indicates that `\setupbackground` takes two arguments, the first of which is an optional list `[...,...]` and the second is a key-value list `[..,..=..,..]`. Moreover we can see that the first argument expects an object of type `NAME` (i.e. a name of some `background`), and that the second argument accepts a variety of keys: `after`, `before`, etc. Also, the second argument inherits all those options that `\setupframed` accepts. Finally, it is defined in the file `pack-bck.mkvi`, and that bit of text is a click-able link to that file.

The colouring of the pop-ups is determined by a file `css/pop_up.css`. Some of the variables in this `css` file are determined by the current colour scheme, so that it can adapt to different schemes. There are also options in `settings/pop_ups`:

  - `on`: a boolean.
  - `line_break`: an integer, or `null`/`false` to never line break.
  - `show_copy_pop_up`: a boolean.
  - `show_source_files`: a boolean.

# Snippets

The main snippets provided are as follows.

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

Additionally, there are the following snippets (which are taken from the ConTeXt samples) which are analogous to the `lorem` snippet that comes out-of-the-box in Sublime Text.

`aesop`, `bryson`, `carey`, `cervantes`, `darwin`, `davis`, `dawkins`, `douglas`, `hawking`, `khatt`, `knuth`, `linden`, `materie`, `montgomery`, `quevedo`, `reich`, `thuan`, `tufte`, `waltham`, `ward`, `weisman`, `zapf`.

# Manuals

In the command palette there is a command `simple_ConTeXt: Open ConTeXt documentation`. It brings up a list of the manuals that normally ship with a ConTeXt installation, and at the bottom of the list is an option to search for a manual not listed. Assuming the file can be located successfully in the TeX tree, it will be opened with the PDF viewer given in `settings/PDF/viewer`.

# Settings

The `.sublime-settings` file for simple_ConTeXt is structured in this way:

```JSON
{
  "settings": {
    "PDF": {"...": "..."},
    "builder": {
      "check": {"...": "..."},
      "program": {
        "name": "...",
        "options": {"...": "..."}
      },
      "options": {
        "...": "..."
      }
    },
    "path": "...",
    "pop_ups": {"...": "..."},
    "references": {"...": "..."}
  },

  "paths": {"...": "..."},
  "PDF_viewers": {"...": "..."},
  "setting_groups": {"...": "..."}
}
```

The main part is everything under `settings`. The `setting_groups` are described some in the [GUI](#via-gui) section. The keys in `PDF_viewers` should be symbolic names, and the values should be either names findable on `$PATH`, or else an absolute path.

In `paths` the keys can be any name, and the values should point to the location of the context binaries (`mtxrun` and such) in a given ConTeXt installation.

## General

Suggested is to add the following to the general Sublime Text settings.

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

That is, add an entry to the `auto_complete_triggers` key like this, for ConTeXt. Then simply typing a backslash <kbd>\\</kbd> in a ConTeXt file will automatically bring up a list of suggested commands, like so:

![autocomplete example][autocomplete]

## Via GUI

The usual way to edit Sublime Text settings is of course to [manually edit](#via-json) the JSON file they live in. For convenience's sake simple_ConTeXt provides another option. In the command palette (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>) there is command `simple_ConTeXt: View/change the settings`. Selecting this brings up a menu for perusing the currently active settings and changing them. Most settings can bechanged quickly and easily in this fashion. For more control, defer to manually editing the JSON.

There is one special provision made for this approach, called `setting_groups`. They can only be edited manually, in the JSON. Here is an example setup from the default settings:

```JSON
{
  "setting_groups": {
    "run_once": {
      "builder": {
        "program": {
          "options": {
            "runs": 1
          }
        }
      }
    },
    "run_to_completion": {
      "builder": {
        "program": {
          "options": {
            "runs": 9
          }
        }
      }
    }
  }
}
```

This says that there should be two groups, `run_once` and `run_to_completion`. On applying the first (which is done by opening the GUI, navigating to `setting_groups/run_once`, and selecting it), the option `settings/builder/program/options/runs` should be set to 1. This setting will eventually get passed as a command-line option `--runs=1` to the `context` program on running the ConTeXt builder, which sets the maximum number of runs to 1.

## Via JSON

To open the `.sublime-settings` file that all the settings are kept at via the menus, under `Preferences/Package Settings/simple_ConTeXt/Settings`, which opens the user settings side-by-side with the default ones. Alternatively, in the command palette select the option `Preferences: simple_ConTeXt Settings`, which has the same effect.

[sublimetext]: https://www.sublimetext.com
[contextgarden]: http://wiki.contextgarden.net/What_is_ConTeXt
[titles]: http://wiki.contextgarden.net/Titles
[metapost]: http://wiki.contextgarden.net/MetaPost
[metafun]: http://wiki.contextgarden.net/MetaFun

[autocomplete]: https://raw.githubusercontent.com/equiva1ence/simple_ConTeXt/master/resources/autocomplete.gif
[completion]: https://raw.githubusercontent.com/equiva1ence/simple_ConTeXt/master/resources/completion.gif
[popup]: https://raw.githubusercontent.com/equiva1ence/simple_ConTeXt/master/resources/popup.png
