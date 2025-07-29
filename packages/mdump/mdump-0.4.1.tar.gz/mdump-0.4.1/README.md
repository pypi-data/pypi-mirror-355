# mdump

A tool for generating project structure documentation in Markdown format.

## Description

`mdump` is a CLI tool that allows you to quickly generate a project overview containing:
- Directory structure (similar to `tree`)
- Contents of all text files
- Automatic ignoring of files listed in `.gitignore`
- Ability to exclude specific folders, files, and extensions
- Automatic copying of results to the clipboard

## Installation

```bash
uv build
uv tool install dist/mdump-*.whl
```

## Usage

```bash
# Dump the current directory
mdump

# Dump a specific directory
mdump ./test-project

# Dump with output saved to a file
mdump --output project-dump.md

# Dump with automatic copying to the clipboard
mdump --clipboard

# Dump excluding specific folders
mdump --exclude-dirs node_modules,dist,build

# Dump excluding specific extensions
mdump --exclude-extensions .pyc,.log,.tmp

# Display help
mdump --help
```

## Options

- `--output, -o`: Save the output to a file instead of displaying it on stdout
- `--clipboard, -c`: Copy the output to the clipboard
- `--exclude-dirs`: Comma-separated list of folders to exclude
- `--exclude-files`: Comma-separated list of files to exclude  
- `--exclude-extensions`: Comma-separated list of extensions to exclude
- `--no-gitignore`: Do not use rules from .gitignore
- `--max-file-size`: Maximum file size to include (default 1MB)
- `--help`: Display help

## Example Output

```markdown
# Project Structure

```
project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── README.md
└── requirements.txt
```

## File Contents

### src/main.py
```python
def main():
    print("Hello, World!")
```

### src/utils.py
```python
def helper_function():
    return "Helper"
```

## License

MIT License
