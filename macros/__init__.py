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
import os
from pathlib import Path

import yaml


def define_env(env):
    """Setup local variables, macros, and filters for mkdocs-macros-plugin."""

    chatter = env.start_chatting('category')
    root_dir = Path(env.conf.config_file_path).parent
    data_dir = root_dir / "data"
    categories_dir = data_dir / "categories"
    documents_dir = data_dir / "documents"

    cat_tree = {}
    for cat in categories_dir.glob("**/*.yaml"):
        with cat.open() as f:
            for doc in yaml.safe_load_all(f):
                if "category" in doc:
                    doc["documents"] = []
                    cat_tree[doc["category"]] = doc
                else:
                    chatter("{} missing category".format(cat))
    for document in documents_dir.glob("**/*.yaml"):
        with document.open() as f:
            for doc in yaml.safe_load_all(f):
                for category in doc.get("categories"):
                    if category in cat_tree:
                        cat_tree[category]["documents"].append(doc)
                    else:
                        chatter(
                            "{}: unknown category '{}'".format(doc, category)
                        )
    env.variables.categories = cat_tree

    @env.macro
    def category(name):
        """Output a category."""
        return env.variables.categories.get(name, {})
