# file-organizer

A simple Python tool to organize files in a directory into categorized folders (Documents, Images, Music, etc.).

## Installation

```sh
pip install file-organizer
```

Or, to install locally from source:

```sh
pip install -e .
```

## Usage

### As a CLI tool

```sh
file-organizer
```

You will be prompted to enter the directory path to organize.

### As a Python module

```python
from file_organizer import organize_files
organize_files('/path/to/your/directory')
```

## License
MIT 
