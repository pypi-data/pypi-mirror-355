"""
Definitions to support evaluation tracing of laziness functionality.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from typing import override

from . import tracing as tr

__all__ = [
    "SuspensionStep", "EvaluationStep", "GettingStep",
]


class SuspensionStep(tr.BaseStep):
    """Class for `Lazy` creation steps.
    """
    def __init__(self, note: str) -> None:
        super().__init__(f"{note}")

    @override
    def __str__(self) -> str:
        return f"Suspend:   {super().__str__()}"


class EvaluationStep(tr.BaseStep):
    """Class for evaluation steps.
    """
    def __init__(self, note: str) -> None:
        super().__init__(f"{note}")

    @override
    def __str__(self) -> str:
        return f"Evaluate:  {super().__str__()}"


class GettingStep(tr.BaseStep):
    """Class for getting steps (from cache).
    """
    def __init__(self, note: str) -> None:
        super().__init__(f"{note}")

    @override
    def __str__(self) -> str:
        return f"Get:       {super().__str__()}"
