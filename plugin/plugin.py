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

import mkdocs


logger = logging.getLogger("mkdocs.plugins.wikimedia")


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
