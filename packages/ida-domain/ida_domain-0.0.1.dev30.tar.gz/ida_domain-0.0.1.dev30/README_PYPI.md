# IDA Domain

[![PyPI version](https://badge.fury.io/py/ida-domain.svg)](https://badge.fury.io/py/ida-domain)
[![Python Support](https://img.shields.io/pypi/pyversions/ida-domain.svg)](https://pypi.org/project/ida-domain/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a **Domain Model** for IDA Pro, allowing seamless interaction with IDA SDK components via Python.

## 🚀 Features

- **Domain Model Interface**: Clean, Pythonic API on top of IDA Python
- **Easy Installation**: Simple pip install from PyPI
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Well Documented**: Comprehensive API reference and examples

## 📦 Installation

### Prerequisites

Set the `IDADIR` environment variable to point to your IDA installation directory:

```bash
export IDADIR="[IDA Installation Directory]"
```

**Example:**
```bash
export IDADIR="/Applications/IDA Professional 9.1.app/Contents/MacOS/"
```

> **Note:** If you have already installed and configured the `idapro` Python package, setting `IDADIR` is not required.

### Install from PyPI

```bash
pip install ida-domain
```

## 🎯 Quick Example

```python
import ida_domain

# Open a binary for analysis
db = ida_domain.Database()
if db.open("path/to/binary"):
    print(f"Entry point: {hex(db.entry_point)}")

    # Iterate through functions
    for func in db.functions.get_all():
        print(f"Function: {func.name} at {hex(func.start_ea)}")

    db.close()
```

## 📝 Advanced Usage Example

Here's a more detailed example showing how to use IDA Domain to analyze a binary:

```python
<!-- TRAVERSE_EXAMPLE_PLACEHOLDER -->
```

## 📖 Documentation

Complete documentation is available at: **https://hexrayssa.github.io/ida-api-domain/**

- **API Reference**: Documentation of available classes and methods
- **Installation Guide**: Detailed setup instructions
- **Examples**: Usage examples for common tasks
- **Getting Started**: Basic guide for new users

For more examples and complete API documentation, visit: https://hexrayssa.github.io/ida-api-domain/

## License

This project is licensed under the MIT License.
