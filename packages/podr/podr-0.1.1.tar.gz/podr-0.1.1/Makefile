.PHONY: help install-dev test lint clean-pyc clean-build clean-test-resources build publish-test publish

# ====================================================================================
# HELP
# ====================================================================================

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  install-dev           Install project in editable mode with dev dependencies"
	@echo "  test                  Run the pytest test suite"
	@echo "  lint                  Run code linters"
	@echo "  build                 Build the package for distribution"
	@echo "  publish-test          Publish the package to the TestPyPI repository"
	@echo "  publish               Publish the package to the official PyPI repository"
	@echo "  clean-pyc             Remove Python file artifacts"
	@echo "  clean-build           Remove build artifacts"
	@echo "  clean-test-resources  Delete the Kubernetes test resources and namespace"


# ====================================================================================
# DEVELOPMENT & PUBLISHING
# ====================================================================================

install-dev:
	pip install -e ".[dev]"

test:
	pytest

lint:
	# Add your preferred linter command here, e.g., flake8 or ruff
	@echo "Linter not yet configured. Please add a linter command."

build: clean-build
	python3 -m build

publish-test: build
	python3 -m twine upload --repository testpypi dist/*

publish: build
	python3 -m twine upload dist/*


# ====================================================================================
# CLEANUP
# ====================================================================================

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -type f -exec rm -f {} +
	find . -name '*.egg' -type d -exec rm -rf {} +

clean-test-resources:
	kubectl delete namespace pod-reaper-test --ignore-not-found=true

clean: clean-build clean-pyc
	@echo "Cleanup complete."