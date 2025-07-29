# UnretiredJS

A Python port of [RetireJS](https://github.com/RetireJS/retire.js) - A tool to scan for vulnerabilities in JavaScript libraries.

[![PyPI](https://img.shields.io/pypi/v/unretiredjs.svg?style=flat-square)](https://pypi.org/project/unretiredjs/)
[![PyPI](https://img.shields.io/pypi/dm/unretiredjs.svg?style=flat-square)](https://pypi.org/project/unretiredjs/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg?style=flat-square)](LICENSE)

## Description

UnretiredJS is a Python library that helps you identify known vulnerabilities in JavaScript libraries used in your web applications. It's a port of the popular RetireJS tool, bringing the same powerful vulnerability scanning capabilities to Python projects.

> **Note**: This is a fork of [FallibleInc/retirejslib](https://github.com/FallibleInc/retirejslib), maintained and updated with additional features and improvements.

## Installation

```bash
pip install unretiredjs
```

## Usage

### Basic Usage

```python
# Method 1: Import specific function
from unretiredjs import scan_endpoint

# Method 2: Import the entire module
import unretiredjs

# Scan a remote JavaScript file
# Using specific import
results = scan_endpoint("http://code.jquery.com/jquery-1.6.min.js")

# Or using full module import
results = unretiredjs.scan_endpoint("http://code.jquery.com/jquery-1.6.min.js")
```

### Sample Output

```python
[
    {
        'detection': 'filecontent',
        'vulnerabilities': [
            {
                'info': [
                    'http://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2011-4969',
                    'http://research.insecurelabs.org/jquery/test/'
                ],
                'identifiers': {
                    'CVE': ['CVE-2011-4969']
                },
                'severity': 'medium'
            }
        ],
        'version': '1.6.0',
        'component': 'jquery'
    }
]
```

## Features

- Scan remote JavaScript files for known vulnerabilities
- Detect vulnerable versions of popular JavaScript libraries
- Comprehensive vulnerability database
- Easy to integrate into Python projects
- Modern Python package structure with src layout

## Requirements

- Python 3.6 or higher
- requests>=2.25.0

## Development

### Project Structure

```
unretiredjs/
├── src/
│   └── unretiredjs/
│       ├── __init__.py
│       ├── retirejs.py
│       ├── vulnerabilities.py
│       └── update_vulnerabilities.py
├── tests/
│   ├── test_retirejs.py
│   ├── test_update_vulnerabilities.py
│   └── compare_results.py
├── pyproject.toml
└── README.md
```

### Vulnerability Data Updates

The vulnerability data used by UnretiredJS is stored in `src/unretiredjs/vulnerabilities.py`. This data is sourced from the official RetireJS repository (`https://raw.githubusercontent.com/RetireJS/retire.js/master/repository/jsrepository.json`).

Updates are handled automatically by a GitHub Action defined in `.github/workflows/update_retirejs_data.yml`. This action runs on a monthly schedule (at 00:00 UTC on the 1st day of every month) to fetch the latest vulnerability information. It also allows for manual triggering via the GitHub Actions UI.

To run the update script manually:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run the update script
python -m unretiredjs.update_vulnerabilities
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Anand Kumar - [GitHub](https://github.com/Anandseth444)