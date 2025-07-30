"""
Utilities to support functional programming in Python.
For internal use only.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
import inspect
from typing import Any, Callable

__all__ = [
    "count_required_args",
    "indent_lines",
    "show_value", "show_args", "force",
]


def count_required_args(f: Callable[..., Any]) -> int:
    """Count the minimum number of required non-keyword arguments of f.
    Does not work for built-in functions (use parameter r of Func to bypass this).
    """
    # N.B. The following does not work, because of a circular import,
    # triggered by the use of the func decorator in basics,
    # which executes already during import and calls count_required_args.
    # from .basics import Func
    # from .laziness import Lazy
    # if isinstance(f, (Func, Lazy)):
    if hasattr(f, '__class__') and f.__class__.__name__ in ('Func', 'Lazy'):
        return 1

    sig = inspect.signature(f)

    def parameter_is_required(p: inspect.Parameter) -> bool:
        return p.default is inspect.Parameter.empty and p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )

    return sum(parameter_is_required(p) for p
               in sig.parameters.values())


def indent_lines(line: str, indentation: str = '', k: int = 0) -> str:
    """Indent each line by n spaces, except for the first k lines.
    """
    lines = line.split('\n')
    return '\n'.join([f"{'' if index < k else indentation}{line}" for index, line in enumerate(lines)])


def show_value(value) -> str:
    """Show value, quoting strings.

    Used in tracing; so, avoid evaluation of lazy objects.
    """
    # print(f"show_value(repr={value!r}, str={value!s})")
    if type(value) is tuple:
        if len(value) == 1:
            return f"({show_value(value[0])},)"
        return f"({', '.join(show_value(v) for v in value)})"
    elif isinstance(value, str):
        return repr(value)
    else:
        return str(value)


def show_args(args: tuple[Any, ...]) -> str:
    """Show tuple as a string, with strings quoted, without trailing comma if singleton.

    N.B. The singleton case does not occur in case of auto-(un)packing of arguments.

    Used in tracing; so, avoid evaluation of lazy objects.
    """
    from FuPy.basics import Left, Right, Func
    from FuPy.fixpoints import Fix
    if not args:
        return "_"
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, (Left, Right, Fix)):
            return f"({arg})"
        elif isinstance(arg, Func):
            return arg.show('.')
        else:
            return show_value(arg)
    else:
        return f"({', '.join(show_value(arg) for arg in args)})"


def force(v: Any) -> Any:
    """Resume all suspended computations.
    """
    if hasattr(v, '__force__'):
        return v.__force__()
    elif isinstance(v, tuple):
        return tuple(force(item) for item in v)
    else:
        return v
