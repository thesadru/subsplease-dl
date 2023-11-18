set windows-shell := ["C:\\Program Files\\Git\\bin\\sh.exe", "-c"]

_default: tasks

# List tasks
tasks:
	@just --list --unsorted

_setup_poetry:
	@poetry install

# SetUp project
setup: _setup_poetry
	@poetry run pre-commit install

# Run ipython
ipython:
	@poetry run ipython

# Run 'ruff'
ruff *args:
	@poetry run ruff {{ args }} .

# Run organize imports and format all code
format:
	@just ruff check --select I --fix
	@just ruff format

# Lint code
lint: format
	@just ruff check

# 'ruff --fix'
ruff-fix:
	@just ruff --fix

# Format and Lint code, and validate poetry 
check: format lint
	@poetry check

# Run program
run *args:
    @poetry run subsplease-dl {{ args }}

# Build project
build: _setup_poetry
	@poetry build

# Install program using pipx
install: build
	@pipx install ./dist/`ls -t dist | head -n2 | grep whl`

# Uninstall program using pipx
uninstall:
	@pipx uninstall subsplease-dl

# Reinstall program using pipx
reinstall: uninstall
	@just install