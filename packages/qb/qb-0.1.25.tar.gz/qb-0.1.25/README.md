# [qb](https://pypi.org/project/qb/)
qb is a functional programming language written in python

## Installation from pypi
```sh
pip install pipx # install pipx
pipx install qb
```

## Building from source
For the build process we use [Poetry](https://python-poetry.org/) and for the installation of packages we use [pipx](https://pypi.org/project/pipx/).

### Setup
```sh
git clone https://github.com/henceiusegentoo/qb-2.0.git
pip install pipx # install pipx
pipx install poetry # use pipx to install poetry
cd qb-2.0
poetry install
```

### Building and Installation
```sh
poetry build --clean # build project
pipx install ./dist/qb-[version]-py3-none-any.whl # install qb on your machine
```
