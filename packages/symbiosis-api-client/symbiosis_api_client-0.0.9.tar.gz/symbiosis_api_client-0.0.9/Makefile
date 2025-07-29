# Python executable and venv paths
PYTHON := python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
UV := uv

.PHONY: venv install install-dev sync lint format typecheck security check-all docs html clean test build publish tox

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(UV) venv $(VENV); \
	else \
		echo "Virtual environment already exists."; \
	fi

# Install project dependencies only (fresh install)
install: venv
	$(UV) pip install --force-reinstall -e .

# Install development dependencies (fresh install)
install-dev: venv
	$(UV) pip install --force-reinstall -e .[dev]
	$(UV) run pre-commit install

# Sync all dependencies using uv (clean sync)
sync: venv
	$(UV) sync --all-groups --refresh

# Run ruff linter
lint: venv
	$(UV) run ruff check src/ tests/
	$(UV) run ruff format --check src/ tests/

# Format code with ruff
format: venv
	$(UV) run ruff format src/ tests/
	$(UV) run ruff check --fix src/ tests/

# Run type checking with mypy
typecheck: venv
	$(UV) run mypy src/symbiosis_api_client tests

# Run security checks with bandit
security: venv
	$(UV) run bandit -r src/ --skip B101

# Run all checks using pre-commit
check-all: venv
	$(UV) run pre-commit run --all-files

# Build documentation
docs: venv
	$(UV) run sphinx-build -b html docs/ docs/_build

# Open the generated HTML documentation in a web browser
html: docs
	open docs/_build/index.html

# Clean up build artifacts and virtual environment
clean:
	rm -rf dist/ docs/_build/ *.egg-info build/
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run tests using pytest
test: venv
	PYTHONPATH=src $(UV) run pytest tests/ -v

# Build package
build: venv
	$(UV) build

# Publish package
publish: venv
	$(UV) publish

# Run tox tests
tox: venv
	$(UV) run tox -e py310,py311,py312,py313,lint
