# Hermes framing nodes
[![PyPI version](https://badge.fury.io/py/hermes-framing-nodes.svg)](https://pypi.org/project/hermes-framing-nodes)

A collection of nodes to provide translation between stream interfaces.

## Installation

### From PyPI

Install the package directly from PyPI using pip:

```bash
pip install hermes-framing-nodes
```

### From Source

Clone the repository and install dependencies:

```bash
git clone https://github.com/node-hermes/hermes-framing-nodes
pip install -e hermes-framing-nodes
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
