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
import pathlib

import polib


def fix_mdpo_locations(lst):
    """Fix up occurrences parsing issue caused by mdpo.

    When mdpo emits a location it includes whitespace which is either
    a violation of the spec or a violation of the expectations of
    polib. Either way, the result is a collection of tuples from the
    parser which will not match tuples generated from parsing an md
    file directly.
    """
    while lst:
        ref = [lst.pop(0)]
        while lst and ":" not in lst[0][0] and lst[0][1] == "":
            # Keep adding tuples until we see one where [0] looks like
            # a "file:loc" part.
            ref.append(lst.pop(0))
        yield tuple(" ".join(o[0] for o in ref).split(":"))


def list_replace(orig, old, new):
    """Recursively replace a value in a list."""
    accum = []
    for item in orig:
        if isinstance(item, list):
            item = list_replace(item, old, new)
        elif isinstance(item, dict):
            item = dict_replace(item, old, new)
        elif isinstance(item, str) or isinstance(item, pathlib.Path):
            if str(item) == str(old):
                item = new
            if not is_url(item):
                item = str(pathlib.Path(item))
        accum.append(item)
    return accum


def dict_replace(orig, old, new):
    """Recusively replace a value in a dict."""
    accum = {}
    for key, value in orig.items():
        if isinstance(value, dict):
            value = dict_replace(value, old, new)
        elif isinstance(value, list):
            value = list_replace(value, old, new)
        elif isinstance(value, str) or isinstance(value, pathlib.Path):
            if str(value) == str(old):
                value = new
            if not is_url(value):
                value = str(pathlib.Path(value))
        accum[key] = value
    return accum


def is_url(value):
    """Does this value look like a URL?"""
    return value.startswith("https://") or value.startswith("http://")


def add_to_po(po, msgid, file, loc):
    """Add a msgid to a PO file."""
    po.append(
        polib.POEntry(msgid=msgid, msgstr="", occurrences=[(file, loc)]),
    )


def add_section_titles_to_po(po, items):
    """Add titles for sections found in nav to the given po."""
    for item in items:
        if item.is_section:
            add_to_po(po, item.title, "mkdocs.yml", "navigation")
            if item.children:
                add_section_titles_to_po(po, item.children)
    return po


def get_message(po, msgid):
    """Get a message from a PO file."""
    # FIXME: if we want fallback languages, we could take a list of PO
    # files here rather than a single file.
    for entry in po:
        if entry.msgid == msgid and entry.msgstr:
            return entry.msgstr
    return msgid
