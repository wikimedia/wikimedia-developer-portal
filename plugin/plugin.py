# Copyright (c) 2022 Wikimedia Foundation and contributors.
# All Rights Reserved.
#
# This file is part of Wikimedia Developer Portal.
#
# Wikimedia Developer Portal is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Wikimedia Developer Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Wikimedia Developer Portal.  If not, see <http://www.gnu.org/licenses/>.
import copy
import datetime
import logging
import math
import os
import pathlib
import shutil
import tempfile

import langcodes

import mdpo.md2po
import mdpo.po2md

import mkdocs

import polib

from . import mdpo_events
from . import util


logger = logging.getLogger("mkdocs.plugins.wikimedia")

LUNR_LANGS = [
    "ar",
    "da",
    "de",
    "en",
    "es",
    "fi",
    "fr",
    "hu",
    "it",
    "ja",
    "nl",
    "no",
    "pt",
    "ro",
    "ru",
    "sv",
    "th",
    "tr",
    "vi",
]


class JinjaWrapperPlugin(mkdocs.plugins.BasePlugin):
    """Wrap markdown files in a jinja template.

    This plugin works in concert with the mkdocs-macros-plugin to setup each
    markdown file as an extension of a "markdown_base.jinja" template prior to
    it being rendered by the macros plugin. This in turn allows us to setup
    common imports and macros for use by all markdown files while keeping
    boilerplate in the markdown files themselves to a minimum.
    """

    def on_page_markdown(self, markdown, page, config, files):
        """Add imports to markdown."""
        return "\n".join(
            [
                "{% extends 'markdown_base.jinja' %}",
                "{% block markdown %}",
                markdown,
                "{% endblock markdown %}",
            ]
        )


class TranslatePlugin(mkdocs.plugins.BasePlugin):
    """Mkdocs plugin for translating content via Gnutext PO files."""

    CONFIG_KEYS = [
        "site_name",
        "site_description",
        "site_author",
        "copyright",
    ]

    META_KEYS = [
        "title",
        "description",
    ]

    def __init__(self, *args, **kwargs):
        """Initialize object."""
        super().__init__(*args, **kwargs)
        self.tmp_dir = None
        self.docs_dir = None
        self.po_files = {}
        self.catalog_file = None
        self.catalog = None
        self.configs = {}
        self.files = {}
        self.alternates = {}

    def on_config(self, config):
        """Add locale information to config."""
        self.tmp_dir = pathlib.Path(tempfile.mkdtemp(suffix=".wmplugin"))
        logger.debug("Created tmp dir %s", self.tmp_dir)

        root_dir = pathlib.Path(config["config_file_path"]).parent
        self.docs_dir = root_dir / config["docs_dir"]
        data_dir = root_dir / "data"
        locale_dir = data_dir / "locale"

        # Scan locale_dir for translation dictionaries
        for p in locale_dir.glob("**/LC_MESSAGES/mkdocs.po"):
            lang = p.parts[len(locale_dir.parts)]
            self.po_files[lang] = str(p)
        logger.debug("Locales found on disk: %s", list(self.po_files.keys()))

        # The English dictionary is our translation catalog
        self.catalog_file = self.po_files.pop("en", None)
        if self.catalog_file is None:
            # Make an empty en catalog if we don't have one yet.
            self.catalog_file = locale_dir / "en" / "LC_MESSAGES" / "mkdocs.po"
            now = datetime.datetime.now(datetime.timezone.utc).isoformat(
                sep=" ", timespec="seconds"
            )
            header_comments = []
            with pathlib.Path(__file__).open() as fh:
                for line in fh:
                    if not line.startswith("#"):
                        break
                    header_comments.append(line.lstrip("# "))
            po = polib.POFile()
            po.header = "".join(header_comments)
            po.metadata = {
                "POT-Creation-Date": now,
                "PO-Revision-Date": now,
                "Language": "en",
                "MIME-Version": "1.0",
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Transfer-Encoding": "8bit",
                "Plural-Forms": "nplurals=2; plural=(n != 1);",
            }
            po.metadata_is_fuzzy = True
            po.save(self.catalog_file)
            self.catalog = po
        else:
            self.catalog = polib.pofile(self.catalog_file)

        for entry in self.catalog:
            # Correct parsing errors in occurrences data
            entry.occurrences = list(
                util.fix_mdpo_locations(entry.occurrences[:])
            )
            # Mark all messages as obsolete. We will toggle this back to False
            # as we merge messages into the catalog so that at the end of the
            # build run we can see which messages are no longer active in the
            # content and remove them.
            entry.obsolete = True
        self.catalog.save()

        # Add locales to config["extra"]["alternate"] to configure locale
        # selector in theme.
        for lang in self.po_files.keys():
            lo = langcodes.Language.get(lang)
            config["extra"]["alternate"].append(
                {
                    "name": lo.display_name(lang).capitalize(),  # Autonym
                    "link": "/{}/".format(lang),
                    "lang": lang,
                }
            )
        self.alternates = copy.deepcopy(config["extra"]["alternate"])

        # Add supported locales to the search plugin config
        search_langs = ["en"]
        for lang in self.po_files.keys():
            if lang in LUNR_LANGS:
                search_langs.append(lang)
        config["plugins"]["search"].config["lang"] = search_langs

        return config

    def on_files(self, files, config):
        """Build parallel data structures for all locales."""
        logger.debug("Extracting translation units from config")
        po = polib.POFile()
        for key in self.CONFIG_KEYS:
            util.add_to_po(po, config[key], "mkdocs.yml", key)

        if "footer_links" in config["extra"]:
            for idx, link in enumerate(config["extra"]["footer_links"]):
                util.add_to_po(
                    po,
                    link["label"],
                    "mkdocs.yml",
                    "extra.footer_links.{}".format(idx),
                )
        self.merge_po_into_catalog(po)

        for lang in self.po_files.keys():
            self.files[lang] = mkdocs.structure.files.Files([])
            self.configs[lang] = self.localize_config(config, lang)

        for file in files:
            src_path = self.docs_dir / file.src_path
            if not src_path.exists():
                # Files sourced from themes and other plugins aren't found in
                # our source tree, so skip them
                continue
            for lang in self.po_files.keys():
                dst_path = self.tmp_dir / lang / file.src_path
                os.makedirs(dst_path.parent, mode=0o755, exist_ok=True)
                shutil.copy(src_path, dst_path)
                self.files[lang].append(
                    mkdocs.structure.files.File(
                        path="{}/{}".format(lang, file.src_path),
                        src_dir=self.tmp_dir,
                        dest_dir=config["site_dir"],
                        use_directory_urls=config["use_directory_urls"],
                    )
                )

        return files

    def localize_config(self, src_config, lang):
        """Create a localized copy of the given config."""
        config = copy.deepcopy(src_config)
        # Preserve orginal plugins object in clones
        config["plugins"] = src_config["plugins"]

        config["theme"]["language"] = lang
        po = self.po_for_lang(lang)
        for key in self.CONFIG_KEYS:
            config[key] = util.get_message(po, src_config[key])

        if "footer_links" in src_config["extra"]:
            flinks = config["extra"]["footer_links"]
            for idx, link in enumerate(src_config["extra"]["footer_links"]):
                flinks[idx]["label"] = util.get_message(po, link["label"])

        # T306672: vary url for header logo nav by locale
        config["extra"]["homepage"] = "/{}/".format(lang)
        return config

    def po_for_lang(self, lang):
        """Get the PO file to use for a language."""
        return polib.pofile(self.po_files.get(lang, self.catalog_file))

    def on_nav(self, nav, config, files):
        """Translate navigation."""
        lang = self.file_language(files.documentation_pages()[0])
        if lang == "en":
            self.extract_nav_translation_units(nav)
        else:
            logger.debug("Translating nav to %s", lang)
            self.translate_nav(nav, lang)

        return nav

    def file_language(self, file):
        """Get the target language for a File."""
        path = pathlib.Path(file.abs_src_path)
        if self.tmp_dir in path.parents:
            loc = path.relative_to(self.tmp_dir)
            return loc.parts[0]
        return "en"

    def extract_nav_translation_units(self, nav):
        """Extract translation units from nav config."""
        logger.debug("Extracting translation units from nav")
        po = util.add_section_titles_to_po(polib.POFile(), nav.items)
        self.merge_po_into_catalog(po)

    def translate_nav(self, nav, lang):
        """Translate navigation."""
        po = self.po_for_lang(lang)

        for item in nav:
            if hasattr(item, "title"):
                item.title = util.get_message(po, item.title)
            if hasattr(item, "children") and item.children:
                self.translate_nav(item.children, lang)
            if item.is_page:
                if not item.file.url.startswith("{}/".format(lang)):
                    item.file.url = "{}/{}".format(lang, item.url)

    def on_page_markdown(self, markdown, page, config, files):
        """Extract translation units or translate markdown."""
        if self.is_translation(page):
            return self.translate_markdown(markdown, page, config, files)
        return self.extract_md_translation_units(markdown, page, config, files)

    def is_translation(self, page):
        """Is the page a translation?"""
        return self.page_language(page) != "en"

    def page_language(self, page):
        """Get the target language for a page."""
        return self.file_language(page.file)

    def translate_markdown(self, markdown, page, config, files):
        """Translate markdown content."""
        po2md = mdpo.po2md.Po2Md(
            self.po_files[self.page_language(page)],
            events={
                "link_reference": mdpo_events.link_reference_event,
            },
            wrapwidth=math.inf,
        )
        return po2md.translate(markdown)

    def extract_md_translation_units(self, markdown, page, config, files):
        """Extract translation units from markdown input."""
        md2po = mdpo.md2po.Md2Po(
            markdown,
            events={
                "msgid": mdpo_events.msgid_event,
                "link_reference": mdpo_events.link_reference_event,
            },
            mark_not_found_as_obsolete=False,
        )
        md2po._current_markdown_filepath = page.file.src_path
        po = md2po.extract()
        # Add translation unit for page.title
        po.insert(
            0,
            polib.POEntry(
                msgid=page.title,
                msgstr="",
                occurrences=[(page.file.src_path, "title")],
            ),
        )
        for key in self.META_KEYS:
            if key in page.meta:
                po.insert(
                    0,
                    polib.POEntry(
                        msgid=page.meta[key],
                        msgstr="",
                        occurrences=[
                            (page.file.src_path, "meta.{}".format(key)),
                        ],
                    ),
                )

        # Merge translation units into catalog
        self.merge_po_into_catalog(po)
        return markdown

    def merge_po_into_catalog(self, po):
        """Merge a po file into our catalog.

        Each message in the given PO file is searched for in our catalog. If
        no match is found, the message is inserted into our catalog. If
        a match is found the occurrences list in the catalog's copy of the
        message is updated to include all occurrences from the new message.
        """
        for entry in po:
            prior = self.catalog.find(
                entry.msgid,
                by="msgid",
                msgctxt=entry.msgctxt,
            )
            if prior is None:
                self.catalog.append(entry)
            else:
                prior.obsolete = False
                for occurrence in entry.occurrences:
                    if occurrence not in prior.occurrences:
                        prior.occurrences.append(occurrence)
        self.catalog.save()

    def on_page_context(self, context, page, config, nav):
        """Localize page metadata and language switcher."""
        lang = self.page_language(page)
        po = self.po_for_lang(lang)
        if lang != "en":
            # Translate page title and metadata
            page.title = util.get_message(po, page.title)
            for key in self.META_KEYS:
                if key in page.meta:
                    page.meta[key] = util.get_message(po, page.meta[key])

        # Make language switcher contextual to current page.
        alts = copy.deepcopy(self.alternates)
        page_url = page.url
        for lang in self.po_files.keys():
            if page.url.startswith("{}/".format(lang)):
                page_url = page.url[len(lang) + 1 :]
                break

        for alt in alts:
            sep = "" if alt["link"].endswith("/") else "/"
            alt["link"] += "{}{}".format(sep, page_url)
        config["extra"]["alternate"] = alts

        return context

    def on_post_build(self, config):
        """Build localized versions."""
        # Run a truncated version of the mkdocs build process for each locale.
        # Largely copied from mkdocs-static-i18n
        for lang in self.po_files.keys():
            logger.info("Building %s site", lang)

            self.update_nav_paths_for_lang(lang)

            config = self.configs[lang]
            config["theme"].language = lang
            env = config["theme"].get_env()
            files = self.files[lang]
            nav = mkdocs.structure.nav.get_navigation(files, config)

            # Fire `on_nav` event
            nav = config["plugins"].run_event(
                "nav",
                nav,
                config=config,
                files=files,
            )

            # Process markdown pages
            logger.debug("Processing markdown files for %s", lang)
            for file in files.documentation_pages():
                mkdocs.commands.build._populate_page(
                    file.page,
                    config,
                    files,
                )

            # Copy static files to build destination
            # FIXME: do we actually need this?
            files.copy_static_files()

            # Render markdown pages to files
            for file in files.documentation_pages():
                mkdocs.commands.build._build_page(
                    file.page,
                    config,
                    files,
                    nav,
                    env,
                )

            # Fire post-build event for search plugin
            config["plugins"]["search"].on_post_build(config)

        self.remove_obsolete_messages()
        self.cleanup_tmp()

    def update_nav_paths_for_lang(self, lang):
        """Update paths in config nav for this language."""
        prefix = "{}/".format(lang)
        for page in self.files[lang].documentation_pages():
            old = page.src_path[len(prefix) :]
            self.configs[lang]["nav"] = util.list_replace(
                self.configs[lang]["nav"],
                old,
                page.src_path,
            )

    def remove_obsolete_messages(self):
        """Remove messages marked as obsolete from catalog."""
        po = polib.POFile()
        po.header = self.catalog.header
        po.fpath = self.catalog.fpath
        po.encoding = self.catalog.encoding
        po.metadata = self.catalog.metadata
        po.metadata_is_fuzzy = self.catalog.metadata_is_fuzzy
        for entry in self.catalog:
            if not entry.obsolete:
                po.append(entry)
        self.catalog = po
        self.catalog.save()

    def cleanup_tmp(self):
        """Remove temporary directory and contents."""
        if self.tmp_dir is None:
            return
        if not self.tmp_dir.exists():
            return
        shutil.rmtree(self.tmp_dir)

    def on_build_error(self, error):
        """Thunk for unhandled errors."""
        self.cleanup_tmp()
