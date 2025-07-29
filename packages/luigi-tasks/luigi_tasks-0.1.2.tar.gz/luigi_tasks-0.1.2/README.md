# Luigi Tasks

A collection of Luigi tasks for data processing.

## Installation

You can install this package from PyPI:

```bash
pip install luigi-tasks
```

Or install directly from the source:

```bash
pip install .
```

## Available Tasks

### HelloTask

A simple task that prints "Hello, World!" and creates a hello.txt file.

```python
from luigi_tasks import HelloTask
import luigi

luigi.build([HelloTask()], local_scheduler=True)
```

### PrintTask

A task that prints a custom message and saves it to a file.

```python
from luigi_tasks import PrintTask
import luigi

# Run with default message
luigi.build([PrintTask()], local_scheduler=True)

# Run with custom message
luigi.build([PrintTask(message="Custom message")], local_scheduler=True)
```

## Using in Docker

To use this package in a Docker container, add the following to your Dockerfile:

```dockerfile
FROM python:3.12-slim

# Install the package
RUN pip install luigi-tasks

# Your other Docker configurations...
```

## Development

To set up the development environment:

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests (if available):
   ```bash
   pytest
   ```

## Building for PyPI

To build and publish to PyPI:

1. Update the version in `pyproject.toml`
2. Build the package:
   ```bash
   python -m build
   ```
3. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```
