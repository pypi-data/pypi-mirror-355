"""
Definitions to support evaluation tracing of basic functionality.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from typing import override
from . import utils
from . import tracing as tr

__all__ = [
    "DefinitionStep", "ApplicationStep", "MotivationStep", "ResultStep",
]


class DefinitionStep(tr.BaseStep):
    """Class for function construction steps.
    """
    def __init__(self, note: str) -> None:
        super().__init__(f"{note}")

    @override
    def __str__(self) -> str:
        return f"Define:    {super().__str__()}"


class ApplicationStep(tr.BaseStep):
    """Class for function application steps.
    """
    def __init__(self, note: str) -> None:
        super().__init__(utils.indent_lines(f"┌ {note}", '│ ', k=1))

    @override
    def __str__(self) -> str:
        return f"Apply:     {super().__str__()}"


class MotivationStep(tr.BaseStep):
    """Class for motivation steps.
    """
    def __init__(self, note: str) -> None:
        super().__init__(utils.indent_lines(f"=   {{ {note} }}", '│     ', k=1))

    @override
    def __str__(self) -> str:
        return f"Motivate:  {super().__str__()}"


class ResultStep(tr.BaseStep):
    """Class for result steps.
    """
    def __init__(self, note: str) -> None:
        super().__init__(utils.indent_lines(f"└ {note}", '  ', k=1))

    @override
    def __str__(self) -> str:
        return f"Return:    {super().__str__()}"
