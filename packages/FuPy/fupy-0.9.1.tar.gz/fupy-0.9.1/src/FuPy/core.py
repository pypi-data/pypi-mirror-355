"""
Core definitions to support functional programming in Python:
:mod:`FuPy.basics`, :mod:`FuPy.tracing`, :mod:`FuPy.laziness`, :mod:`FuPy.fixpoints`,
and finally :mod:`FuPy.operator` as `op`.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from . import operator_ as op  # noqa
from .basics import *  # noqa
from .basics import __all__ as basics_all
from .fixpoints import *  # noqa
from .fixpoints import __all__ as fixpoints_all
from .laziness import *  # noqa
from .laziness import __all__ as laziness_all
from .tracing import trace  # noqa
from .tracing_basics import *  # noqa
from .tracing_basics import __all__ as tracing_basics_all
from .tracing_laziness import *  # noqa
from .tracing_laziness import __all__ as tracing_laziness_all
from .utils import force  # noqa

# Sphinx needs __all__ for its automodule functionality
__all__ = basics_all + ["op", "trace", "force"] + tracing_basics_all + laziness_all + tracing_laziness_all + fixpoints_all
