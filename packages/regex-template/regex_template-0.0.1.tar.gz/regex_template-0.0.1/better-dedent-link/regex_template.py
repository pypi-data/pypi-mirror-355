import re
from string import Formatter
from string.templatelib import Interpolation

# https://discuss.python.org/t/add-convert-function-to-string-templatelib/94569/10
_convert = classmethod(Formatter.convert_field).__get__(Formatter)


def compile(template, flags=0, verbose=True):
    if verbose:
        flags |= re.VERBOSE
        parts = []
    for item in template:
        match item:
            case Interpolation(value, _, conversion, format_spec):
                value = _convert(value, conversion)
                if format_spec == "safe":
                    parts.append(value)
                else:
                    parts.append(re.escape(format(value, format_spec)))
            case _:
                parts.append(item)
    return re.compile("".join(parts), flags=flags)


if __name__ == "__main__":
    name = "Trey"
    regex = compile(rt"""
        ({name})
        \d+
    """)
    print(regex.sub(r"\1", "Trey3"))
