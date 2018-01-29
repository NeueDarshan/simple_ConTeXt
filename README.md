# Introduction

This [Sublime Text][sublime-text] 3 package provides some support for working with the [ConTeXt][context-introduction] program.

I started this project for my personal use, because I wanted some quality of life features for writing ConTeXt documents in Sublime Text. Since there were no packages that fit the bill, I started to write my own. Over time I felt that the result was looking pretty good, so I put it out into the world for the hopeful benefit of other ConTeXt users.

That said, I can only test that things work on my machine, so some bugs are to be expected. Furthermore I only have so much spare time to work on it, and it's a hobby project. Don't expect a super polished experience!

Currently the features are:
  - syntax file(s)
  - builder(s)
  - command auto-completions
  - command pop-ups
  - snippet file(s)
  - manual opener
  - other bits and bobs

# Installation/Setup

Install via [package control][package-control], under the name `simple_ConTeXt`. Afterwards, there are some optional things to set up.

  - Open the simple ConTeXt settings file via `Preferences: simple_ConTeXt Settings` in the command palette or `Preferences/Package Settings/simple_ConTeXt/Settings` in the menu bar. Under the `paths` key, put in a key-value entry for the ConTeXt installation on your machine: the key can be whatever string you like, and the value should be the path to the context binaries. For example:

    ```JSON
    {
      "paths": {
        "main": "/home/user-name/.local/context/tex/texmf-linux-64/bin"
      }
    }
    ```

    For opening PDFs after building a ConTeXt file, and opening the manuals, the `PDF_viewers` entry is consulted. Similarly to the previous, the keys can be any string, but each value should be the name of a PDF viewer program. (In the case of Sumatra PDF viewer, this could be simply `sumatraPDF` if it's on your environment path, or else an explicit path like `/usr/bin/sumatraPDF`.)

 - Add the following entry to your general Sublime Text (ST) settings, in order to get automatic completions for ConTeXt commands on typing the initial backslash <kbd>\\</kbd>.

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

 - Consider adding the following to your key bindings: it will (for ConTeXt files only) replace the binding for the local symbol list (<kbd>Ctrl</kbd>+<kbd>R</kbd>) with a custom variation of it. The idea is to make it easier to navigate between headings, definitions, references, and file inclusions (`\input` and the like).

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

 - Consider adding the following to your ConTeXt syntax specific settings:

    ```JSON
    {
      "spell_check": true,
      "spelling_selector": "text.tex.context - (meta.control-word.context, meta.environment.math.context, meta.brackets.context, source, markup.raw, comment)"
    }
    ```

    This should do a pretty decent job at limiting spell check to the appropriate places only (e.g. not in maths or code blocks).

# Builders

The main builder is of course the ConTeXt one, that is a wrapper around the `context` binary. But, as it's easy to do so, there are a couple others:
  - Lua (using LuaTeX as a Lua interpreter);
  - MetaPost.

For MetaPost, there are two variants. Firstly, just use the version of `mpost` that ships with a ConTeXt installation. Alternatively, use `context` itself: when called on a MetaPost file, it will compile it (using the MetaFun format) into a PDF.

# Misc

Completions should play well with others, e.g. the completions provided by the [Unicode​Completion][unicode-​completion] package. (Although Unicode​Completion is intended for LaTeX, I still find it useful for ConTeXt as many of the command names are the same.)

[context-introduction]: http://wiki.contextgarden.net/What_is_ConTeXt
[package-control]:      https://packagecontrol.io
[sublime-text]:         https://www.sublimetext.com
[unicode-​completion]:   https://github.com/randy3k/UnicodeCompletion
