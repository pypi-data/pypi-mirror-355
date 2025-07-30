# Hermes Core

[![PyPI version](https://badge.fury.io/py/node-hermes-core.svg)](https://pypi.org/project/node-hermes-core)

Core libary for the Node Hermes project.

## Installation

### From PyPI

Install the package directly from PyPI using pip:

```bash
pip install node-hermes-core
```

### From Source

Clone the repository and install dependencies:

```bash
git clone https://github.com/node-hermes/hermes-core
pip install -e node-hermes-core
```

## Development

This project depends on UV for managing dependencies.
Make sure you have UV installed and set up in your environment.

You can find more information about UV [here](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv venv
```

```bash
uv sync --all-extras --dev
```
