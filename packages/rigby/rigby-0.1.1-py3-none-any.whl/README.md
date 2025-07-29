# rigby

<img src="images/rigby.webp" alt="Rigby" width="200"/>

https://pypi.org/project/rigby/

A Python tool to remove empty lines and clean up whitespace in Python files, with a special focus on removing unnecessary empty lines within functions.

## Installation

Simply run:
```bash
pip install rigby
```

That's it! All dependencies will be automatically installed.

## Usage

You can use rigby either as a command-line tool or as a library in your Python code.

### Command Line Usage

```bash
# Clean a single file
rigby run file.py

# Clean multiple files
rigby run file1.py file2.py

# Clean all Python files in a directory
rigby run .
```

### Python Usage

```python
from rigby import clean_file

# Clean a single file
clean_file("path/to/your/file.py")
```

## Features

- Removes empty lines within functions
- Preserves necessary whitespace for Python syntax
- Maintains code readability while reducing unnecessary spacing
- Supports both single file and directory processing
- Can be used as a CLI tool or Python library

## Dependencies

All of these will be installed automatically when you install the package:
- click>=8.0.0 - For command line interface
- loguru>=0.7.0 - For logging
- pydantic>=2.0.0 - For data validation
- typing-extensions>=4.0.0 - For type hints
- rich>=13.0.0 - For beautiful terminal output

## License

MIT License

rm -rf dist/ && python3 -m build
python3 -m twine upload dist/*
pip uninstall -y rigby && pip install --no-cache-dir rigby