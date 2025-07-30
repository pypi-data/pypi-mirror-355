# path_helper

## Description

This simple package provides a helper function to import modules from a path.


## Tests

To run the tests, use the following command:

```bash

$ tox
...

```

## Usage

```python

# Import the package to automatically add the most likely package path to sys.path
import pfun_path_helper

# ... or use the helper functions directly
from pfun_path_helper import get_lib_path, append_path, guess_package_root

```
