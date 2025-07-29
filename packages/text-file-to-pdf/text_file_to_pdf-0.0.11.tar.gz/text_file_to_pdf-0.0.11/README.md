# Text File to PDF

[<img src="https://img.shields.io/badge/GitHub-TruckCab%2Ftext--file--to--pdf-blue.svg?logo=Github">](https://github.com/TruckCab/text-file-to-pdf)
[![text-file-to-pdf-ci](https://github.com/TruckCab/text-file-to-pdf/actions/workflows/ci.yml/badge.svg)](https://github.com/TruckCab/text-file-to-pdf/actions/workflows/ci.yml)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/text-file-to-pdf)](https://pypi.org/project/text-file-to-pdf/)
[![PyPI version](https://badge.fury.io/py/text-file-to-pdf.svg)](https://badge.fury.io/py/text-file-to-pdf)
[![PyPI Downloads](https://img.shields.io/pypi/dm/text-file-to-pdf.svg)](https://pypi.org/project/text-file-to-pdf/)

The `text-file-to-pdf` is a command-line utility that allows you to convert text files into PDF format. It supports various configurations such as page orientation, units, font type, font size, and margins.

## Install package
You can install `text-file-to-pdf` from source.

### Option 1 - from PyPi
```shell
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
. .venv/bin/activate

pip install text-file-to-pdf
```

### Option 2 - from source - for development
```shell
git clone https://github.com/TruckCab/text-file-to-pdf.git

cd text-file-to-pdf

# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
. .venv/bin/activate

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install text-file-to-pdf - in editable mode with dev dependencies
pip install --editable .[dev]
```

### Note
For the following commands - if you running from source and using `--editable` mode (for development purposes) - you will need to set the PYTHONPATH environment variable as follows:
```shell
export PYTHONPATH=$(pwd)/src
```

## Usage
### Help
```shell
text-file-to-pdf --help
Usage: text-file-to-pdf [OPTIONS]

Options:
  --version / --no-version        Prints the "Text File to PDF" program
                                  version and exits.  [required]
  --input-file TEXT               The input text file to convert to PDF
                                  format.  The path can be relative or
                                  absolute.  [required]
  --output-file TEXT              The output PDF file to create.  The path can
                                  be relative or absolute.  [required]
  --orientation [portrait|landscape]
                                  The page orientation to use for the PDF
                                  file.  [required]
  --unit [pt|mm|cm|in]            The units to use for the PDF.  [default: mm;
                                  required]
  --format [a3|a4|a5|letter|legal]
                                  The page (paper) format for the PDF file.
                                  [default: letter; required]
  --font-name [courier|helvetica|times]
                                  The font to use in the PDF file.  [default:
                                  courier; required]
  --font-size INTEGER             The font-size to use in the PDF file.
                                  [default: 9; required]
  --left-margin FLOAT             The left margin for the PDF - in cm.
                                  [default: 5.669291338582678; required]
  --top-margin FLOAT              The top margin for the PDF - in cm.
                                  [default: 9.921259842519683; required]
  --help                          Show this message and exit.
```

## Handy development commands

#### Version management

##### Bump the version of the application - (you must have installed from source with the [dev] extras)
```bash
bumpver update --patch
```
