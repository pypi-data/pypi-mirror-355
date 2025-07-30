# load env variables
set dotenv-load

# env variables
TESTPYPI_TOKEN := env('TESTPYPI_TOKEN')
PYPI_TOKEN := env('PYPI_TOKEN')
PYPI_PROJECT := "depsize"
IMPORT_PROJECT := "depsize"


# list recipes
@default: 
    just --list

# install and compile requirements txt files for main and dev dependencies
@install:
    mkdir -p requirements
    mkdir -p data
    uv sync --frozen
    uv pip compile pyproject.toml -o requirements/main.txt # main deps only
    uv pip compile --group dev -o requirements/dev.txt # dev 

# install editable version for local development
@edit-install:
    uv pip install -e .

# update dependencies in lockfile
@update:
    uv lock --upgrade
    uv pip compile pyproject.toml -o requirements/main.txt # main deps only
    uv pip compile --group dev -o requirements/dev.txt # dev 

# check for type errors
@check:
    ruff check

# format code
@format:
    ruff format

# test package can be imported
@package-test:
    uv run --with {{PYPI_PROJECT}} --no-project -- python -c "import {{IMPORT_PROJECT}}"

# build package
@build: check format package-test
	rm -rf dist/; \
	uv build

# publish on python package index
pypi_publish:
    uv publish --token {{PYPI_TOKEN}}

# publish on test python package index
testpypi_publish:
    uv publish --index testpypi --token {{TESTPYPI_TOKEN}}
