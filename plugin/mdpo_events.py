# Copyright (c) 2021 Wikimedia Foundation and contributors.
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
import logging


logger = logging.getLogger("mkdocs.plugins.wikimedia.mdpo_events")


def msgid_event(mdpo_instance, msgid, *args):
    """Handle mdpo msgid event callbacks."""
    if msgid.startswith(": "):
        mdpo_instance._disable_next_line = True


def link_reference_event(mdpo_instance, target, *args):
    """Handle mdpo link_reference event callbacks."""
    if target.startswith("^"):
        # Footnotes are treated as text blocks, so they will be translated
        # elsewhere.
        return False
