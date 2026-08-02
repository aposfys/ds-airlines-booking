# DS Airlines — developer entry points.
#
# Two ways to run this project. `make up` uses Docker and needs nothing else
# installed. Everything below `make db-start` runs it natively against a
# PostgreSQL cluster kept inside this repo, for when Docker is not available.
#
#   make check      everything CI runs, in one command
#   make dev        API on :8000 and interface on :5173
#
.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV       := backend/.venv
PY         := $(VENV)/bin/python
PIP        := $(VENV)/bin/pip
PGDATA     := .pgdata
PGPORT     := 55432
PGHOST     := /tmp
PGBIN      := $(shell brew --prefix postgresql@17 2>/dev/null)/bin
DB         := dsairlines
TESTDB     := dsairlines_test

export DATABASE_URL      ?= postgresql+asyncpg://$(USER)@/$(DB)?host=$(PGHOST)&port=$(PGPORT)
export TEST_DATABASE_URL ?= postgresql+asyncpg://$(USER)@/$(TESTDB)?host=$(PGHOST)&port=$(PGPORT)
export SECRET_KEY        ?= local-development-key-not-for-any-real-deployment

# ── Help ──────────────────────────────────────────────────
help:
	@echo "DS Airlines"
	@echo
	@echo "  Docker (nothing else needed):"
	@echo "    make up            build and run the whole stack"
	@echo "    make down          stop it"
	@echo
	@echo "  Native (needs postgresql@17, python3, node 22):"
	@echo "    make setup         create the venv, install everything, start the db"
	@echo "    make dev           run API :8000 and interface :5173"
	@echo "    make seed          load demo flights and an admin account"
	@echo
	@echo "  Checks:"
	@echo "    make check         tests + lint + build + contrast (what CI runs)"
	@echo "    make test          backend suite only"
	@echo "    make contrast      WCAG check on the AF palette"
	@echo
	@echo "  Database:"
	@echo "    make db-start / db-stop / db-reset / psql"

# ── Docker ────────────────────────────────────────────────
up:
	@test -f .env || { echo "Copy .env.example to .env first, and set SECRET_KEY and POSTGRES_PASSWORD."; exit 1; }
	docker compose up --build

down:
	docker compose down

# ── Native setup ──────────────────────────────────────────
setup: $(VENV) frontend/node_modules db-start migrate
	@echo
	@echo "Ready. 'make seed' for demo data, then 'make dev'."

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r backend/requirements.txt

frontend/node_modules:
	cd frontend && npm ci

# ── Database ──────────────────────────────────────────────
# The cluster lives in .pgdata inside the repo, so it cannot collide with any
# PostgreSQL you already run and is deleted with the working tree.
db-start:
	@command -v $(PGBIN)/initdb >/dev/null 2>&1 || { \
		echo "postgresql@17 not found. Install it with: brew install postgresql@17"; \
		echo "Or use Docker instead: make up"; exit 1; }
	@if [ ! -d "$(PGDATA)" ]; then \
		echo "Initialising cluster in $(PGDATA)"; \
		$(PGBIN)/initdb -D $(PGDATA) -U $(USER) --auth=trust --locale=C >/dev/null; \
	fi
	@# Distinguish "our cluster is already up" from "something else owns the
	@# port" — the latter otherwise surfaces as an opaque pg_ctl failure.
	@if ! $(PGBIN)/pg_ctl -D $(PGDATA) status >/dev/null 2>&1; then \
		if lsof -ti :$(PGPORT) >/dev/null 2>&1; then \
			echo "Port $(PGPORT) is already in use by PID $$(lsof -ti :$(PGPORT) | head -1)."; \
			echo "Stop it, or set PGPORT to something else."; exit 1; \
		fi; \
		$(PGBIN)/pg_ctl -D $(PGDATA) -o "-p $(PGPORT) -k $(PGHOST)" -l $(PGDATA)/server.log start; \
	fi
	@sleep 1
	@$(PGBIN)/psql -h $(PGHOST) -p $(PGPORT) -U $(USER) -d postgres -tAc \
		"SELECT 1 FROM pg_database WHERE datname='$(DB)'" | grep -q 1 || \
		$(PGBIN)/createdb -h $(PGHOST) -p $(PGPORT) -U $(USER) $(DB)
	@$(PGBIN)/psql -h $(PGHOST) -p $(PGPORT) -U $(USER) -d postgres -tAc \
		"SELECT 1 FROM pg_database WHERE datname='$(TESTDB)'" | grep -q 1 || \
		$(PGBIN)/createdb -h $(PGHOST) -p $(PGPORT) -U $(USER) $(TESTDB)
	@echo "PostgreSQL up on port $(PGPORT)"

db-stop:
	@$(PGBIN)/pg_ctl -D $(PGDATA) stop 2>/dev/null || echo "not running"

db-reset: db-stop
	rm -rf $(PGDATA)
	@$(MAKE) db-start migrate

psql:
	@$(PGBIN)/psql -h $(PGHOST) -p $(PGPORT) -U $(USER) -d $(DB)

migrate:
	cd backend && ../$(VENV)/bin/alembic upgrade head

# ── Running ───────────────────────────────────────────────
dev: db-start migrate
	@echo "API      http://localhost:8000      (docs at /docs)"
	@echo "Interface http://localhost:5173"
	@trap 'kill 0' EXIT; \
	(cd backend && ../$(VENV)/bin/uvicorn main:app --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

# Credentials are overridable, but there are no silent defaults in the
# application itself — these exist only to make a local database usable.
SEED_ADMIN_EMAIL    ?= ops@dsairlines.example
SEED_ADMIN_PASSWORD ?= changeme-locally-1

seed: db-start migrate
	@cd backend && SEED_ADMIN_EMAIL=$(SEED_ADMIN_EMAIL) \
		SEED_ADMIN_PASSWORD=$(SEED_ADMIN_PASSWORD) \
		../$(VENV)/bin/python scripts/seed.py
	@echo "Administrator: $(SEED_ADMIN_EMAIL) / $(SEED_ADMIN_PASSWORD)"

# ── Checks ────────────────────────────────────────────────
check: test lint build contrast
	@echo
	@echo "All checks passed."

test: db-start
	cd backend && ../$(VENV)/bin/python -m pytest -q

lint:
	cd frontend && npm run lint

build:
	cd frontend && npm run build

contrast:
	$(PY) docs/brand/contrast_check.py

clean:
	rm -rf $(VENV) frontend/node_modules frontend/dist

.PHONY: help up down setup db-start db-stop db-reset psql migrate dev seed \
        check test lint build contrast clean
