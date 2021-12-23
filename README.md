Wikimedia Developer Portal
==========================

Static site generator for a portal to Wikimedia technical documentation.

## Quick start

Clone this repository, start the local development server, and update the build to preview changes.

```console
$ git clone https://gerrit.wikimedia.org/r/wikimedia/developer-portal
$ cd developer-portal
$ make start
$ open http://127.0.0.1:9000/

$ vim src/index.md
$ make build
$ open http://127.0.0.1:9000/
```

NOTE: `open` is a MacOS command to open a file, directory, or url in the
default application for that media type. On a Linux host you can either
manually open the URL or use a similar URL opening script like `xdg-open`,
`sensible-browser`, `x-www-browser`, or `gnome-open`.

## How it works

### Rendering page content

* In /data/documents: YAML data describes key documents.
* Each document is assigned to one or more categories.
* In /data/categories: YAML describes the categories.
* /macros/__init__.py : Macro builds categories from YAML files.
* Markdown files reside in /src subdirectories that correspond to the top-level sections of the dev portal site.
* Jinja template syntax inside those markdown files pulls in content from the categories.

### Rendering the navigation

* The Material theme for Mkdocs generates [navigation sections](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-sections) based on the documents in a given subdirectory. It renders tables of contents based on the structure of an individual markdown file (its headings).
* The `navigation.indexes` setting in mkdocs.yml implements [section index pages](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#section-index-pages). This causes the index.md file for a directory to be used as the landing page for a section. We use this feature because our index.md files (in /src) only include links to the other pages in the directory, so we don't need or want them to be displayed as an additional item to click in the left nav.
*  While it could be simpler to use a single markdown file for each site section, and rely on the TOC for navigation, this has drawbacks:
    *  The TOC disappears on small screens, effectively removing navigation to key subsections.
    *  Using multiple markdown files enables navigation through and between site sections via buttons at the bottom of the screen.  This is a nice additional navigation option to supplement the left and/or horizontal menus.
    *  Using a single index.md file populated via YAML for each site section means that nearly all the site structure will be rendered via YAML and templates. This means a larger number of YAML files, and a more difficult structure to understand if you're encountering the site for the first time. It's easier to understand how the site is rendered -- and thus better for future maintainers -- when more of the structure is coming from markdown and less from YAML and Jinja magic.
    *  For more details about why we made these implementation decisions, see [this Miro board](https://miro.com/app/board/o9J_lkldIfg=/?moveToWidget=3074457367215289187&cot=14)

## License

Wikimedia Developer Portal code and configuration is licensed under the [GNU GPLv3+][] license. Textual content is licensed under the [CC-BY-SA 3.0][] license.

[GNU GPLv3+]: https://www.gnu.org/copyleft/gpl.html
[CC-BY-SA 3.0]: https://creativecommons.org/licenses/by-sa/3.0/

## Instructions for documentarians

The Material theme for Mkdocs renders content in ways that can be confusing due to our usage of templates to generate page content based on yaml docs and categories (see the `data` subdirectory).

This section describes the content requirements that doc editors and creators must follow in order for the site to render correctly and consistently.

### Hide TOC in subdirectory index files

`index.md` files in subdirectories of the `src` directory must hide the table of contents. This is necessary because the content of most of these pages is navigational: the section headers in the page mirror the list of other pages in the directory/navigation section, so the `navigation` and the `toc` render the same content. This is only true for subdirectories of the `src` directory -- not for the top-level `index.md` nor for any other markdown files.

To hide the table of contents, include the following at the top of the index.md file:

```md
---
hide:
  - toc
---
```
### Mirror text copy in index files and category files

In general (but not always), each section (`##`) in a subdirectory index.md file should contain:

* A text snippet that is the same as the category description used in the Jinja template on the subpage to which that section links
* A link to another md file (subpage) in that directory

<!--TODO: add examples to make this clearer -->
