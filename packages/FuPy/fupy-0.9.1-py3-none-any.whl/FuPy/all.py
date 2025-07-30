"""
Load all `FuPy` functionality.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from .core import *
from .prelude import *
#
# Sphinx needs __all__ for its automodule functionality
from .core import __all__ as core_all
from .prelude import __all__ as prelude_all

__all__ = core_all + prelude_all
