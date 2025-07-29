#!/usr/bin/env python3

'''
Helper pymodule used by eda_deps_bash_completion.bash, extracts valid
targets from DEPS files
'''

import sys
import os
import json

import yaml
import toml

from opencos.deps_helpers import get_deps_markup_file

def get_markup_table_keys(partial_path='./') -> list:
    '''Returns a list of root level keys for DEPS.[yml|yaml|toml|json]

    Does not include DEFAULTS.
    '''
    partial_target = ''
    if not partial_path or partial_path == '.':
        partial_path = './'

    if not os.path.exists(partial_path):
        partial_path, partial_target = os.path.split(partial_path)
    if not partial_path:
        partial_path = './'

    filepath = get_deps_markup_file(base_path=partial_path)
    if not filepath:
        # Couldn't find a DEPS file, let bash completion handle it (with -W words or -G glob)
        return []

    data = {}
    _, file_ext = os.path.splitext(filepath)
    try:
        if file_ext in ['', '.yml', 'yaml']:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        elif file_ext == '.toml':
            data = toml.load(filepath)
        elif file_ext == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except Exception: # pylint: disable=broad-exception-caught
        return []

    if not isinstance(data, dict):
        # We found a DEPS file, but it wasn't a table/dict so we can't return root keys
        return []

    # Try to resolve path/to/target/partial_target_
    # -- prepend path information to found targets in path/to/target/DEPS
    prepend = ''
    if partial_path and partial_path != './':
        prepend = partial_path
        if not partial_path.endswith('/'):
            prepend += '/'

    # Return the list of keys w/ prepended path information, and don't include
    # uppercase strings like 'DEFAULTS' or 'METADATA'
    return [
        prepend + x for x in list(data.keys()) if x.startswith(partial_target) and not x.isupper()
    ]


def main() -> None:
    '''Returns None, prints DEPS keys space separated, uses sys.argv for a single
    partial path arg (DEPS file to examine)'''

    if len(sys.argv) > 1:
        partial_path = sys.argv[1]
    else:
        partial_path = './'
    keys = get_markup_table_keys(partial_path)
    print(" ".join(keys))

if __name__ == "__main__":
    main()
