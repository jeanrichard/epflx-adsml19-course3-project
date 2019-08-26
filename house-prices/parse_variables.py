# -*- coding: utf-8 -*-
"""\
Utilities to extract the definitions of the variables from 'documentation.txt'.
"""

# Standard library:
import json
import re
import typing as T

# 3rd party:
from yaml import dump
try:
    from yaml import CDumper as Dumper
except ImportError:  # fall back to pure Python
    from yaml import Dumper

P_QUALITATIVE = re.compile(r'''
    (?P<name>[^(]+)            # the name, including leading and trailing white spaces
    \(                         # '('
    (?P<kind>Nominal|Ordinal)  # the kind is either 'Nominal' or 'Ordinal'
    \)\s*:                     # '):'
''', re.VERBOSE)

P_VALUE = re.compile(r'''
    [ ]{7}                     # 7 blank spaces
    (?P<value>[^\t]+)          # the value, including leading and trailing white spaces
    \t                         # a tabulation
''', re.VERBOSE)

P_QUANTITATIVE = re.compile(r'''
    (?P<name>[^(]+)                # the name, including leading and trailing white spaces
    \(                             # '('
    (?P<kind>Discrete|Continuous)  # the kind is either 'Discrete' or 'Continuous'
    \)\s*:                         # '):'
''', re.VERBOSE)


def parse_definitions(path: str) -> T.List[T.Dict[str, T.Any]]:
    """\
    Parses definitions from a file.

    Args:
        path: The path to the file to parse.
    """
    definitions = []
    with open(path, 'r', encoding='latin-1') as f:
        in_definition = False
        values = []
        for line in f:
            # Skip empty lines:
            if len(line.strip()) == 0:
                continue

            # The same line can end a definition and start a new one:
            if in_definition:
                m = P_VALUE.match(line)
                if m:
                    # This is a valid value:
                    values.append(m.group('value').strip())
                else:
                    # This ends the definition of a qualitative variable:
                    definition = {
                        'name': name,
                        'kind': kind,
                        'values': values
                    }
                    definitions.append(definition)
                    in_definition = False
                    values = []

            if not in_definition:
                m = P_QUALITATIVE.match(line)
                if m:
                    # This starts the definition of a qualitative variable:
                    name = m.group('name').strip()
                    kind = m.group('kind').strip()
                    in_definition = True
                    
                m = P_QUANTITATIVE.match(line)
                if m:
                    # This is the definition of a quantitative variable:
                    name = m.group('name').strip()
                    kind = m.group('kind').strip()
                    definition = {
                        'name': name,
                        'kind': kind
                    }
                    definitions.append(definition)

    return definitions


def dump_json(definitions, filename):
    """\
    Save in JSON format.
    """
    with open(filename, 'w') as f:
        # Use indented representation instead of compact one:
        json.dump(definitions, f, indent=4)


def dump_yaml(definitions, filename):
    """\
    Save in YAML format.
    """
    with open(filename, 'w') as f:
        dump(definitions, stream=f, Dumper=Dumper, default_flow_style=False)


if __name__ == '__main__':
    definitions = parse_definitions('documentation.txt')
    dump_json(definitions, 'variables.json')
#     dump_yaml(definitions, 'variables.yaml')
