SHELL := /bin/bash
PYTHON := $$(which python3)
PIP := $$(which pip3)
PYTEST := $$(which pytest)
PROJECT_NAME := pyschematron
GIT_BRANCH := $$(git branch --show-current)
PROJECT_VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)

.PHONY: help
help:
	@echo "clean: remove all build, test, coverage and Python artifacts (no uninstall)"
	@echo "test(s): run unit and integration tests with the default Python."
	@echo "test-unit: run the unit tests using the default Python."
	@echo "test-integration: run the integration tests using the default Python."
	@echo "test-all: run all tests using all environments using tox"
	@echo "docs: generate Sphinx HTML documentation, including API docs"
	@echo "docs-pdf: generate the PDF documentation, including API docs"
	@echo "docs-man: generate the linux manpages"
	@echo "docs-changelog: generate the changelog documentation"
	@echo "install-deps: install all the dependencies"
	@echo "install-symlink: install the package as a symlink, to allow continuous development"
	@echo "uninstall: uninstall PySchematron (while keeping the dependencies)"
	@echo "prepare-release: prepare for a new release"
	@echo "release: package and release the new version"


.PHONY: clean
clean: clean-build clean-pyc clean-test

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	rm -rf .tox/
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache
	rm -rf tests/htmlcov
	rm -rf tests/.coverage
	find tests -name 'build' -exec rm -rf {} +
	find tests -name '.coverage' -exec rm -rf {} +


.PHONY: tests
tests: test

.PHONY: test
test:
	mkdir -p build
	COVERAGE_FILE=build/.coverage \
	$(PYTEST) tests --cov=$(PROJECT_NAME) --cov-report=html:build/coverage/defaultenv --cov-report=term --html=build/pytest/report-defaultenv.html --self-contained-html

.PHONY: test-unit
test-unit:
	mkdir -p build
	COVERAGE_FILE=build/.coverage \
	$(PYTEST) tests/unit --cov=$(PROJECT_NAME) --cov-report=html:build/coverage/defaultenv --cov-report=term --html=build/pytest/report-defaultenv.html --self-contained-html

.PHONY: test-integration
test-integration:
	mkdir -p build
	COVERAGE_FILE=build/.coverage \
	$(PYTEST) tests/integration --cov=$(PROJECT_NAME) --cov-report=html:build/coverage/defaultenv --cov-report=term --html=build/pytest/report-defaultenv.html --self-contained-html

.PHONY: test-all
test-all:
	tox

.PHONY: docs
docs:
	mkdir -p build
	rm -f docs/$(PROJECT_NAME)*.rst
	rm -f docs/modules.rst
	$(MAKE) -C docs clean
	sphinx-apidoc -o docs/ $(PROJECT_NAME)
	$(MAKE) -C docs html SPHINXBUILD='python3 $(shell which sphinx-build)'
	@echo "To view results type: firefox docs/_build/html/index.html &"

.PHONY: docs-pdf
docs-pdf:
	mkdir -p build
	rm -f docs/$(PROJECT_NAME)*.rst
	rm -f docs/modules.rst
	$(MAKE) -C docs clean
	sphinx-apidoc -o docs/ $(PROJECT_NAME)
	$(MAKE) -C docs latexpdf SPHINXBUILD='python3 $(shell which sphinx-build)'
	@echo "To view results use something like: evince docs/_build/latex/$(PROJECT_NAME).pdf &"

.PHONY: docs-man
docs-man:
	rm -f docs/$(PROJECT_NAME)*.rst
	rm -f docs/modules.rst
	$(MAKE) -C docs clean
	sphinx-apidoc -o docs/ $(PROJECT_NAME)
	$(MAKE) -C docs man SPHINXBUILD='python3 $(shell which sphinx-build)'
	@echo "To view results use something like: man docs/_build/man/$(PROJECT_NAME).1 &"


.PHONY: docs-changelog
docs-changelog:
	gitchangelog


.PHONY: prepare-release
prepare-release: clean
	@echo "Current version: "$(PROJECT_VERSION)
	@while [ -z "$$NEW_VERSION" ]; do \
        read -r -p "Give new version: " NEW_VERSION;\
    done && \
    ( \
        printf 'Setting new version: %s \n\n' \
        	"$$NEW_VERSION " \
	) && sed -i 's/version = \"\(.*\)\"/version = "'$$NEW_VERSION'"/g' pyproject.toml
	$(MAKE) docs-changelog
	@echo "Consider manually inspecting CHANGELOG.rst for possible improvements."

.PHONY: release
release: clean release-git release-pip

.PHONY: release-git
release-git:
	git add -u
	git diff-index --quiet HEAD || git commit -am "New release"
	git push
	git tag -a v$(PROJECT_VERSION) -m "Version $(PROJECT_VERSION)"
	git push origin --tags

.PHONY: release-pip
release-pip:
	flit publish

.PHONY: dist
dist: clean
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	ls -l dist

.PHONY: install-deps
install-deps:
	flit install --only-deps

.PHONY: install-symlink
install-symlink:
	flit install --symlink

.PHONY: uninstall
uninstall:
	$(PIP) uninstall -y $(PROJECT_NAME)
