# MMTSP

MMTSP: Automate mmt sri and push commands with commit message and configurable prefix.

## Installation

```bash
pip install gd-mmtsp
```

## Usage

```bash
mmtsp --set-prefix "GD**: "
```

```bash
mmtsp -m "Commit message"
```
or 
```bash
mmtsp --message "Commit message"
```

Use prefix from argument
```bash
mmtsp --prefix "GD**: "
```

Skip SRI generation
```bash
mmtsp --no-sri
```

## Upload to PyPI

1. Clone this repository locally
2. Do some changes
3. Run tests (optional) or create a new tests
4. Build the package
```bash
python3 -m build
```

5. Upload the package to PyPI
```bash
python3 -m twine upload dist/*
```

Note: You need to have a ~/.pypirc file with your PyPI credentials.

Also login to PyPI with your credentials. Find credentials in notebook TW.
[PyPI Package Index](https://pypi.org/project/gd-mmtsp/)