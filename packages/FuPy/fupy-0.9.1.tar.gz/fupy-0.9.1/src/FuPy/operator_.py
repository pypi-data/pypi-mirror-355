"""
Definitions of `Func`-wrapped operators from the standard :mod:`operator` library.
All docstrings are included.
Operator variants with leading and trailing '__' are not provided.

It also defines `Func`-wrapped versions of the type constructors :class:`bool`, :class:`int`, and :class:`str`,
named `bool_`, `int_`, and `str_`.
Keep in mind that calling these `Func`-wrapped constructors without argument
is now equivalent to calling them with :const:`FuPy.basics.unit` as argument.

Note that `__all__` is created dynamically from `operator.__all__`.
So, code completion may not work as expected, because tools cannot
statically see from the source code which names are exported.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
import operator
from .basics import func
from .laziness import evaluate

__all__ = operator.__all__

for name in __all__:
    attr = getattr(operator, name)
    if callable(attr):
        globals()[name] = func(attr).doc(f"{attr.__doc__}\n(`Func`-wrapped version)")
    # else:
    #     print(f"WARNING: skipped {name}")

bool_ = func(lambda x: bool(evaluate(x)), name="bool_"
             ).doc("`Func`-wrapped version of `bool()`.\n"
                   "N.B. `bool_()` is interpreted as `bool_(unit)`, which returns `False`.")
land = func(lambda a, b: evaluate(a) and evaluate(b), name="∧"
            ).doc("`Func`-wrapped version of `lambda a, b: a and b` (logical and).")
lor = func(lambda a, b: evaluate(a) or evaluate(b), name="∨"
           ).doc("`Func`-wrapped version of `lambda a, b: a or b` (logical or).")
int_ = func(lambda x: int(x), name="int_"
            ).doc("`Func`-wrapped version of `int()`.\n"
                  "N.B. `int_()` is interpreted as `int_(unit)`, which raises a `TypeError`.")
str_ = func(lambda x: str(x), name="str_"
            ).doc("`Func`-wrapped version of `str()`."
                  "N.B. `str_()` is interpreted as `str_(unit)`, which returns '_'.")

__all__.extend(['bool_', 'land', 'lor', 'int_', 'str_'])

# Cleanup the namespace by deleting the import and the original function
del operator, func
