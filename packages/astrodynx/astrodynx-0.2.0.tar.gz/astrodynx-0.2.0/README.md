![GitHub License](https://img.shields.io/github/license/pennbay/astrodynx)
[![CI](https://github.com/pennbay/astrodynx/actions/workflows/ci.yml/badge.svg)](https://github.com/pennbay/astrodynx/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pennbay/astrodynx/graph/badge.svg?token=CeIVlgbcAs)](https://codecov.io/gh/pennbay/astrodynx)
![PyPI - Version](https://img.shields.io/pypi/v/astrodynx)


# AstroDynX

A modern astrodynamics library powered by JAX: differentiate, vectorize, JIT to GPU/TPU, and more.

## Features
- JAX-based fast computation
- Pre-commit code style and type checks
- Continuous testing
- Automated versioning and changelog
- GitHub Actions for CI/CD

## Installation
```bash
pip install astrodynx
```

## Usage
Check version
```python
import astrodynx as adx
print(adx.__version__)
```


## Development
Initialize
```bash
pip install -e .[dev]
pre-commit install
```
After code change
```bash
pytest
```
```bash
git add .
pre-commit
cz c
git push -u origin main --tags
```

## Build Docs
```bash
pip install -e .[docs]
sphinx-build -b html docs docs/_build/html
```
