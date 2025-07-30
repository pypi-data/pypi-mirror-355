"""
Definitions to support evaluation tracing of functional programs in Python.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, override, Optional
from abc import ABC, abstractmethod
from . import utils

__all__ = [
    "Trace",
    "BaseStep",
    "TracingTerminated",
    "trace_step", "inc_depth", "dec_depth", "trace",
]


@dataclass
class Trace:
    """A Trace object contains a sequence of evaluation (rewrite) steps.
    """
    trace: list["BaseStep"] = field(default_factory=list)
    depth: int = 0
    skip_steps: set[type["BaseStep"]] = field(default_factory=set)  # suppressed steps in __str__ and live tracing
    max_steps: int = None  # unbounded

    # @override
    # def __repr__(self) -> str:
    #     return repr(f"trace={self.trace}")

    def __str__(self) -> str:
        return '\n'.join(f"{index:4} {step}" for index, step in enumerate(self.trace) if type(step) not in self.skip_steps)

    def log(self, step: "BaseStep") -> None:
        """Append a step to the trace.
        """
        self.trace.append(step.set_depth(self.depth))

    def update_depth(self, delta: int) -> None:
        """Update the depth for the next step.
        """
        self.depth += delta


@dataclass
class BaseStep(ABC):
    """Abstract Base Class for all Trace steps.
    """
    note: str
    depth: int = 0

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(note={self.note!r}, depth={self.depth})"

    @override
    def __str__(self) -> str:
        indentation = self.depth * '│     '
        return f"{indentation}{utils.indent_lines(self.note, f"{16 * ' '}{indentation}", k=1)}"

    def set_depth(self, depth: int) -> "BaseStep":
        """Set the depth of the step.
        """
        self.depth = depth
        return self


class TracingTerminated(Exception):
    """Exception to indicate early termination of an expression evaluation.

    Typically, this is because the maximum number of steps was reached.
    """
    pass


# the global trace; assign Trace() to clear it and enable tracing
the_trace: Optional[Trace] = None
live_tracing: bool = False  # TODO: Why not incorporated in Trace?


def trace[A](expr: Callable[[], A],
             live: Optional[bool] = None,
             skip_steps: Optional[set[type[BaseStep]]] = None,
             max_steps: Optional[int] = None) -> tuple[A|Exception, Trace]:
    """Trace evaluation of expr.
    The expression must be provided as a constant function,
    that is, in the form `lambda: expr`, or as `Lazy(lambda: expr)`.
    Later, possibly also as string.
    """
    global the_trace, live_tracing
    live_tracing_old = live_tracing
    the_trace = Trace()
    if live is not None:
        live_tracing = live
    if skip_steps is not None:
        the_trace.skip_steps = skip_steps
    if max_steps is not None:
        the_trace.max_steps = max_steps

    try:
        if live:
            print()  # ensure that trace output starts in column 1
        result = expr(), the_trace
    except Exception as e:
        result = e, the_trace
    finally:
        live_tracing = live_tracing_old
        the_trace = None

    return result


def trace_step(step_: Callable[[], BaseStep]) -> None:
    """Add step_() to the trace if tracing is enabled.
    For internal use only.
    """
    global the_trace, live_tracing
    if the_trace is None:
        return
    index = len(the_trace.trace)
    if live_tracing and the_trace.max_steps and index >= the_trace.max_steps:
        raise TracingTerminated(f"Exceeding {the_trace.max_steps} steps")
    step = step_()
    the_trace.log(step)
    if live_tracing and type(step) not in the_trace.skip_steps:
        print(f"{index:4} {step}")


def inc_depth() -> None:
    """Increment the tracing depth by one.
    """
    global the_trace
    if the_trace is not None:
        the_trace.update_depth(1)


def dec_depth() -> None:
    """Decrement the tracing depth by one.
    """
    global the_trace
    if the_trace is not None:
        the_trace.update_depth(-1)
