#!/usr/bin/env python3

import sys
import inspect
from pathlib import Path

from .cli import cli
from .logic import NOT_GIVEN, DEFAULT_FILE_NAME, File
from . import git

# This bit of code is duplicated in logic.py.
# This is because of the fact that this code looks at itself and finds the path of the file containing the code.
stack = None
try:
    stack = inspect.stack()
    this_code_file_path = stack[0].filename
    for frame in stack:
        caller_path = frame.filename
        if caller_path != this_code_file_path and "frozen" not in caller_path.lower():
            break
finally:
    del stack
repo_root = git.find_repo_path(caller_path or ".")
if repo_root:
    datafile_path = Path(repo_root) / DEFAULT_FILE_NAME
else:
    datafile_path = NOT_GIVEN

default_file = File(path=datafile_path)
super(File, default_file).__setattr__("__spec__", __spec__)
super(File, default_file).__setattr__("cli", cli)

# Hack. This replaces the module "hardcoded" with an instance of the class File.
# Now you can do this to use the default settings (.hardcoded.yml, secret, ask if not found):
# import hardcoded
# login(hardcoded.password)

sys.modules[__name__] = default_file
