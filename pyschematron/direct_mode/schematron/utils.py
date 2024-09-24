__author__ = 'Robbert Harms'
__date__ = '2023-03-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

import re


def macro_expand(string: str, macros: dict[str, str]) -> str:
    """Expand the provided macros on the provided string.

    This replaces all the macros in one go. This is a specialized version of multi-string replacement which
    assumes all the replacements are unique (as they are in macro's).

    We use this function for instantiating abstract patterns to concrete patterns.

    This assumes the macros already have the prefix `$`.

    Args:
        string: the string on which to apply the macro
        macros: the macros to expand

    Returns:
        A version of the string with the macros expanded
    """
    macros_pattern = '|'.join(re.escape(k) for k in macros)
    pattern = re.compile(f'({macros_pattern})\\b')
    return pattern.sub(lambda match: macros[match.group(0)], string)
