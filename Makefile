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

this := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
PROJECT_DIR := $(dir $(this))
PIPELINE_DIR := $(PROJECT_DIR)/.pipeline
# Prefer Compose v2, but allow override on hosts that only have v1
COMPOSE ?= docker compose

help:
	@echo "Make targets:"
	@echo "============="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'
.PHONY: help

# FIXME: reenable dockerfile rebuild after blubber is fixed
# start: .env  ## Start the docker-compose stack
start: .env  ## Start the docker-compose stack
	DOCKER_DEFAULT_PLATFORM=linux/amd64 $(COMPOSE) up --build --detach
.PHONY: start

stop:  ## Stop the docker-compose stack
	$(COMPOSE) stop
.PHONY: stop

restart: stop start  ## Restart the docker-compose stack
.PHONY: restart

status:  ## Show status of the docker-compose stack
	$(COMPOSE) ps
.PHONY: status

shell:  ## Get an interactive shell inside the container
	$(COMPOSE) exec portal /bin/bash
.PHONY: shell

tail:  ## Tail logs from the docker-compose stack
	$(COMPOSE) logs -f
.PHONY: tail

test: lint build
	$(COMPOSE) exec portal git diff --no-ext-diff --compact-summary --exit-code data/locale/en/LC_MESSAGES/mkdocs.po
.PHONY: test

lint:
	$(COMPOSE) exec portal sh -c " \
		poetry check \
		&& poetry run flake8 \
		&& poetry run black --check --diff . \
	"
.PHONY: lint

build:  ## Build static site
	$(COMPOSE) exec portal poetry run mkdocs --verbose build
.PHONY: build
docs: build
.PHONY: docs

format-code:  ## Reformat Python files
	$(COMPOSE) exec portal poetry run black .
.PHONY: format-code

clean:  ## Clean up Docker images and containers
	yes | docker image prune
	yes | docker container prune
.PHONY: clean

.env:  ## Generate a .env file for local development
	./bin/make_env.sh ./.env
