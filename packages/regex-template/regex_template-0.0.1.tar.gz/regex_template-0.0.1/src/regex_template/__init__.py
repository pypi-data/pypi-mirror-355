# SPDX-FileCopyrightText: 2025-present Trey Hunner
#
# SPDX-License-Identifier: MIT
"""regex_template - Compiled regular expressions with auto-escaped interpolations"""

import re
from string import Formatter
from string.templatelib import Interpolation, Template


__all__ = ["compile"]


# https://discuss.python.org/t/add-convert-function-to-string-templatelib/94569/10
_convert = classmethod(Formatter.convert_field).__get__(Formatter)


def compile(template, flags=0, verbose=True):
    """
    Compile a regular expression with auto-escaped interpolations.

    Only accepts t-string Templates. Automatically escapes interpolated values
    unless they use the :safe format specifier.

    Args:
        template: A t-string Template to compile
        flags: Regular expression flags (same as re.compile)
        verbose: If True, adds re.VERBOSE flag for readable patterns

    Returns:
        A compiled regular expression Pattern object

    Raises:
        TypeError: If template is not a Template object (t-string)
    """
    if not isinstance(template, Template):
        raise TypeError(
            f"regex_template.compile() only accepts t-string Templates, "
            f"got {type(template).__name__}. Use re.compile() for regular strings."
        )

    if verbose:
        flags |= re.VERBOSE

    # Process t-string Template
    parts = []
    for item in template:
        match item:
            case Interpolation(value, _, conversion, format_spec):
                value = _convert(value, conversion)
                if format_spec == "safe":
                    parts.append(str(value))
                else:
                    formatted_value = format(value, format_spec)
                    parts.append(re.escape(str(formatted_value)))
            case _:
                parts.append(item)
    return re.compile("".join(parts), flags=flags)

