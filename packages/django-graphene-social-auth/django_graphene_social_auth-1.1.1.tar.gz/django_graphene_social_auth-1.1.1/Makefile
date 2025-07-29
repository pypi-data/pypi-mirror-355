
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  test        Runs tests"
	@echo "  test-all    Runs tests using tox"
	@echo "  coverage    Runs tests with coverage"
	@echo "  lint        Runs linting"
	@echo "  format      Formats code with black and isort"
	@echo "  release     Makes a release"

test:
	@pytest tests

coverage:
	@pytest\
		--verbose\
		--cov graphql_social_auth\
		--cov-config pyproject.toml\
		--cov-report term\
		--cov-report xml

lint:
	@flake8 graphql_social_auth tests

format:
	@black graphql_social_auth tests
	@isort graphql_social_auth tests

test-all:
	@tox

release:
	@python -m build
	@python -m twine upload dist/*

.PHONY: help test coverage lint format test-all release
