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

## License

Wikimedia Developer Portal code and configuration is licensed under the [GNU GPLv3+][] license. Textual content is licensed under the [CC-BY-SA 3.0][] license.

[GNU GPLv3+]: https://www.gnu.org/copyleft/gpl.html
[CC-BY-SA 3.0]: https://creativecommons.org/licenses/by-sa/3.0/
