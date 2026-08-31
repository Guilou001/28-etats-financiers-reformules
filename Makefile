# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 22 tests fermés, sans réseau
	$(UV) run pytest

lint:
	$(UV) run ruff check .

data:             ## le tableau de Statistique Canada, 63 Mo (réseau requis)
	$(UV) run efr fetch

all: data         ## tout : données, identités, ensemble, industries et figures
	$(UV) run efr tout
