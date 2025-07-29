# Default Python version (for Docker tests)
PYTHON_VERSION := 3.13
UV_PATH := $(shell which uv 2>/dev/null)
# Whether to use UV for installation
UV_INSTALL := 1

.PHONY: help
help:
	@echo "Usage: make <target> [option]"
	@echo "\nTargets:"
	@echo "  install [UV_INSTALL]    Install this package"
	@echo "  docs    Build Sphinx documentation"
	@echo "  test    Run unit tests"
	@echo "  coverage    Build an HTML coverage report"
	@echo "  lint    Run 'ruff' linting on project"
	@echo "  docker-test [PYTHON_VERSION]    Run unit tests in Docker container"
	@echo "\nSpecial Targets:"
	@echo "  docker-test-all    Runs unit tests in Docker containers across all versions of Python"

# Install UV if it is not installed already.
.PHONY: uv-init
uv-init:
	@if [ -z "$(UV_PATH)" ]; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi

.PHONY: install
install:
	@if [ $(UV_INSTALL) -eq 1 ]; then\
		$(MAKE) uv-init && uv sync && echo "Please run the following to activate the virtualenv:" && echo " source .venv/bin/activate";\
	else\
		python -m pip install .;\
	fi

.PHONY: docs
docs: uv-init
	@uv run --group docs sphinx-build -b html docs/source/ docs/build/html/

.PHONY: test
test: uv-init
	@uv run --group test coverage run -m unittest discover test/

.PHONY: coverage
test-coverage: test
	@uv run --group test coverage html

.PHONY: lint
lint: uv-init
	@uv run --group test ruff check src/iblox/

.PHONY: docker-test-all
docker-test-all:
	@$(MAKE) docker-test PYTHON_VERSION=3.9
	@$(MAKE) docker-test PYTHON_VERSION=3.10
	@$(MAKE) docker-test PYTHON_VERSION=3.11
	@$(MAKE) docker-test PYTHON_VERSION=3.12
	@$(MAKE) docker-test PYTHON_VERSION=3.13

# Run unit tests in a Docker Python container
.PHONY: docker-test
docker-test:
	@echo "Testing Python:$(PYTHON_VERSION)"
	@docker run -it --rm -e UV_LINK_MODE="copy" -v "$(PWD)":/usr/src/app -w /usr/src/app python:$(PYTHON_VERSION)\
		sh -c 'python -m pip install uv && uv run --group test python -m unittest discover ./test/'