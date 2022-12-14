SHELL := /bin/bash
PYTHON := $$(which python3)
PIP := $$(which pip3)
PYTEST := $$(which pytest)
GIT_BRANCH := $$(git branch --show-current)
PROJECT_NAME := pyschematron
PROJECT_VERSION := $$(python -c 'from pyschematron import __version__; print(__version__)')

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
	@echo "prepare-release: prepare for a new release"
	@echo "zip: create the zip file used for the release"
	@echo "release: package and release the new version"


.PHONY: clean
clean: clean-build clean-pyc clean-test
	$(PYTHON) setup.py clean

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
	rm -f docs/$(PROJECT_NAME)*.rst
	rm -f docs/modules.rst
	$(MAKE) -C docs clean
	sphinx-apidoc -o docs/ $(PROJECT_NAME)
	$(MAKE) -C docs html SPHINXBUILD='python3 $(shell which sphinx-build)'
	@echo "To view results type: firefox docs/_build/html/index.html &"

.PHONY: docs-pdf
docs-pdf:
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
release: clean release-git

.PHONY: release-git
release-git:
	git add -u
	git diff-index --quiet HEAD || git commit -am "New release"
	git push
	git tag -a v$(PROJECT_VERSION) -m "Version $(PROJECT_VERSION)"
	git push origin --tags

.PHONY: zip
zip:
	mkdir -p build
	rm -rf build/*
	zip build/$(ZIP_BASENAME)-v$(PROJECT_VERSION).zip -r application.py analysis_worker requirements.txt Procfile .platform
	cp build/$(ZIP_BASENAME)-v$(PROJECT_VERSION).zip build/$(ZIP_BASENAME)-deploy.zip

.PHONY: release-pip
release-pip:
	$(PYTHON) setup.py sdist bdist_wheel
	twine upload dist/$(PROJECT_NAME)-$(PROJECT_VERSION).tar.gz dist/$(PROJECT_NAME)-$(PROJECT_VERSION)-py3-none-any.whl

.PHONY: dist
dist: clean
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	ls -l dist

.PHONY: install
install: dist
	$(PIP) install --upgrade --no-deps --force-reinstall dist/$(PROJECT_NAME)-*.tar.gz

.PHONY: uninstall
uninstall:
	$(PIP) uninstall -y $(PROJECT_NAME)
