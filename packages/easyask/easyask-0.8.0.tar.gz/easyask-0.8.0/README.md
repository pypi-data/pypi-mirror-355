[![CI](https://github.com/Y-Square-T3/easyask/actions/workflows/ci.yml/badge.svg)](https://github.com/Y-Square-T3/easyask/actions/workflows/ci.yml)
[![Publish Docker Hub](https://github.com/Y-Square-T3/easyask/actions/workflows/publish-image.yml/badge.svg)](https://hub.docker.com/repository/docker/sheltonsuen/easyask/general)
[![Publish PyPI](https://github.com/Y-Square-T3/easyask/actions/workflows/publish-pypi.yml/badge.svg)](https://pypi.org/project/easyask/)

# easyask

easyask is a minimal demonstration package intended to show how chart options can be generated programmatically.

## Quick start

```python
from easyask.tools import chart

# Build an option for a bar chart
option = chart.get_chart_options([
        ['Matcha Latte', 43.3, 85.8, 93.7],
        ['Milk Tea', 83.1, 73.4, 55.1],
        ['Cheese Cocoa', 86.4, 65.2, 82.5],
        ['Walnut Brownie', 72.4, 53.9, 39.1]
    ], ['product', '2015', '2016', '2017'])

print(option)
```

## Python version

This project requires **Python 3.12** or newer, as specified in `pyproject.toml`.

## Running the demo

To see the package in action, run the demonstration module:

```bash
python -m easyask
```

Example scripts are also available in the `examples/` directory.

## How to test

```bash
PYTHONPATH=. uv run pytest
```
