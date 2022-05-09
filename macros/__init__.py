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
from pathlib import Path

import yaml


def define_env(env):
    """Setup local variables, macros, and filters for mkdocs-macros-plugin."""
    chatter = env.start_chatting("local")
    root_dir = Path(env.conf.config_file_path).parent
    data_dir = root_dir / "data"
    categories_dir = data_dir / "categories"
    documents_dir = data_dir / "documents"

    cat_tree = {}
    doc_tree = {}
    # Collect all category descriptions from filesystem
    for category_file in categories_dir.glob("**/*.yaml"):
        with category_file.open() as f:
            for category in yaml.safe_load_all(f):
                if "category" in category:
                    category["documents"] = []
                    cat_tree[category["category"]] = category
                else:
                    chatter("{} missing category".format(category_file))
    # Collect all document descriptions from filesystem and associate with
    # categories
    for document_file in documents_dir.glob("**/*.yaml"):
        with document_file.open() as f:
            for document in yaml.safe_load_all(f):
                doc_tree[document_file.stem] = document

                if "categories" in document:
                    cats = document.get("categories")
                    if isinstance(cats, list):
                        # Convert legacy list of category names into dict of
                        # name:sortidx pairs. The default sortidx is 0.
                        cats = {category: 0 for category in cats}
                    for category, sortidx in cats.items():
                        if category in cat_tree:
                            cat_tree[category]["documents"].append(
                                (sortidx, document["title"], document)
                            )
                        else:
                            chatter(
                                "{}: unknown category '{}'".format(
                                    document,
                                    category,
                                )
                            )
    # Sort document collections for each category
    for category in cat_tree.keys():
        cat_tree[category]["documents"] = [
            document
            for sortidx, title, document in sorted(
                cat_tree[category]["documents"]
            )
        ]
    env.variables.categories = cat_tree
    env.variables.documents = doc_tree

    @env.macro
    def category_data(name):
        """Get the data for a category."""
        return env.variables.categories.get(name, {})

    @env.macro
    def document_data(name):
        """Get the data for a document."""
        return env.variables.documents.get(name, {})
