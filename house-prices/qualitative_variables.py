# -*- coding: utf-8 -*-
"""\
Utilities to extract the definitions of the qualitative variables from 'documentation.txt'.
"""

# Standard library:
import json
import re

P_QUANTITATIVE = re.compile(r'''
    (?P<name>[^(]+)            # the name, including leading and trailing white spaces
    \(                         # '('
    (?P<kind>Nominal|Ordinal)  # the kind is either 'Nominal' or 'Ordinal'
    \):                        # '):'
''', re.VERBOSE)

P_VALUE = re.compile(r'''
    [ ]{7}                     # 7 blank spaces
    (?P<value>[^\t]+)          # the value, including leading and trailing white spaces
    \t                         # a tabulation
''', re.VERBOSE)


def parse_definitions(path):
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
            
            if in_definition:
                m = P_VALUE.match(line)
                if m:
                    # This is a value:
                    values.append(m.group('value').strip())
                else:
                    # This is the end of the current definition:
                    definition = {
                        'name': name,
                        'kind': kind,
                        'values': values
                    }
                    definitions.append(definition)
                    in_definition = False
                    values = []
            
            if not in_definition:
                m = P_QUANTITATIVE.match(line)
                if m:
                    # This is the start of a new definition:
                    name = m.group('name').strip()
                    kind = m.group('kind').strip()
                    in_definition = True
            
    return definitions


if __name__ == '__main__':
    definitions = parse_definitions('documentation.txt')
    # Save as JSON:
    with open('qualitative_variables.json', 'w') as f:
        json.dump(definitions, f)
