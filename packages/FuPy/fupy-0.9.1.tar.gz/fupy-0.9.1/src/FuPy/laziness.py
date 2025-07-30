"""
Definitions to support lazy expressions.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from typing import Callable, Optional, override, Any
from functools import total_ordering

from . import tracing as tr
from . import utils
from .basics import *
from .basics import OperatorSection
from .tracing_laziness import *

__all__ = [
    "Lazy", "IterLazy", "evaluate", "lazy", "lazyf",
    "fpower_lazy", "fpower_left_lazy",
]


@total_ordering
class Lazy[A]:
    """A lazy expression of type A, with memoization upon evaluation.

    Thunks are identified by a sequence number.
    Also keeps track of statistics:
    * How often its value has been requested.
    * How deep evaluation unnested lazy expressions.

    See: https://en.wikipedia.org/wiki/Lazy_evaluation.
    A.k.a. as thunk: https://en.wikipedia.org/wiki/Thunk.
    Sharing of lazy expressions is encouraged, since they need to be evaluated only once.

    Usage:

    - Construct by `v = Lazy(lambda: expression)`

      N.B. The lambda captures local names occurring in expression, in its closure.

    - Get value by `evaluate(v)`; for internal use only: `v._get()`

    """
    next_thunk_number = 0
    # full_regime = False  # laziness regime: full or minimal

    def __init__(self, value: Callable[[], A] | A, name: Optional[str] = None) -> None:
        self.value = value  # unevaluated expression or cached evaluation result of the expression
        self.name = name
        self.nesting_count = 0  # number of times that nested Lazy expression is copied
        self.hit_count = 0  # number of times the cached value was used; 0 means unevaluated
        self.thunk_number = Lazy.next_thunk_number
        Lazy.next_thunk_number += 1
        tr.trace_step(lambda: SuspensionStep(f"{self}"))

    @override
    def __repr__(self) -> str:
        if self.nesting_count:
            nesting_state = f", nesting_count={self.nesting_count}"
        else:
            nesting_state = ""
        if self.hit_count:
            state = f"value={utils.show_value(self.value)}, thunk_number={self.thunk_number}{nesting_state}, hit_count={self.hit_count}"
        else:
            state = f"unevaluated={self.name or '`...`'}, thunk_number={self.thunk_number}"
        return f"Lazy({state})"

    def __str__(self) -> str:
        if self.hit_count:
            status = f"= {utils.show_value(self.value)}"
        else:
            status = f": {self.name or '`...`'}"
        return f"⟨θ_{self.thunk_number} {status}⟩"

    def __force__(self) -> "Lazy[A]":
        return utils.force(self._get())

    # def show(self, op: str) -> str:
    #     """Return name in the context of operator `op`, adding parentheses if needed.
    #     """
    #     # TODO: Still used?
    #     print(f"{self!r}.show({op!r})")
    #     if op:
    #         return f"({self})"
    #     return str(self)

    def _get(self) -> A:
        """Evaluate lazy value, with caching/memoization.
        Repeats until the result is not Lazy.
        This can be used as a trampoline to implement tail call elimination.
        """
        unevaluated = not self.hit_count
        nesting_comment = ""

        while unevaluated:
            tr.trace_step(lambda: EvaluationStep(f"{self}{nesting_comment}"))
            tr.inc_depth()
            self.value = self.value()  # take off lambda: wrapper; result could be Lazy again
            tr.dec_depth()
            if isinstance(self.value, Lazy):  # flatten, avoiding recursion (that would burden the stack)
                self.nesting_count += 1
                nesting_comment = f" {{nesting count: {self.nesting_count}, θ_{self.value.thunk_number}}}" if self.nesting_count else ''
                unevaluated = not self.value.hit_count
                self.name = self.value.name
                self.value = self.value.value
            else:
                unevaluated = False

        self.hit_count += 1
        tr.trace_step(lambda: GettingStep(f"{self}"))
        return self.value

    def __call__[A, B](self: "Lazy[Callable[[A], B]]", *args, **kwargs) -> "Lazy[B]":
        """Apply as function.

        Assumption: self is Func instance

        For Weak Head Normal Form, the function itself is evaluated first.
        """
        # if Lazy.full_regime:
        #     return Lazy[B](lambda: lambda a: self._get()(a))
        # else:
        self._get()
        if not callable(self.value):
            raise TypeError(f"value in {self!r} is not callable")
        return self.value(*args, **kwargs)  # wrap this in Lazy again?

    def __bool__(self) -> bool:
        return bool(self._get())

    def __eq__(self, other):
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        return self._get() == evaluate(other)

    def __lt__(self, other):
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        return self._get() < evaluate(other)

    def __add__(self, other):
        # if Lazy.full_regime:
        #     print("LAZY ADD")
        #     return Lazy(lambda: self._get() + other)
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return func(self) + other
        if isinstance(other, Lazy):
            return Lazy(lambda: self._get() + other._get())  # apply (_ + other) under self
        return self._get() + evaluate(other)

    def __radd__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: other + self._get())
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return other + func(self)
        if isinstance(other, Lazy):
            return Lazy(lambda: other._get() + self._get())  # apply (other + _) under self
        return evaluate(other) + self._get()

    def __sub__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: self._get() - other)
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        return self._get() - evaluate(other)

    def __rsub__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: other - self._get())
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        return evaluate(other) + self._get()

    def __mul__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: self._get() * other)
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return func(self) * other
        if isinstance(other, Lazy):
            return Lazy(lambda: self._get() * other._get(), name=f"{self} * {other}")  # apply (_ * other) under self
        return self._get() * evaluate(other)

    def __rmul__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: other * self._get())
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return other * func(self)
        if isinstance(other, Lazy):
            return Lazy(lambda: other._get() * self._get())  # apply (other * _) under self
        return evaluate(other) * self._get()

    def __matmul__(self, other):
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return func(self) @ other
        if isinstance(other, Lazy):
            return Lazy(lambda: self._get() @ other._get())  # apply (_ @ other) under self
        return self._get() @ other

    def __rmatmul__(self, other):
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return other @ func(self)
        if isinstance(other, Lazy):
            return Lazy(lambda: other._get() @ self._get())  # apply (other @ _) under self
        return other @ self._get()

    def __or__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: self._get() | other)
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return func(self) | other
        if isinstance(other, Lazy):
            return Lazy(lambda: self._get() | other._get())  # apply (_ | other) under self
        return self._get() | evaluate(other)

    def __ror__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: other | self._get())
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return other | func(self)
        if isinstance(other, Lazy):
            return Lazy(lambda: other._get() | self._get())  # apply (other | _) under self
        return evaluate(other) | self._get()

    def __and__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: self._get() & other)
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return func(self) & other
        if isinstance(other, Lazy):
            return Lazy(lambda: self._get() & other._get())  # apply (_ & other) under self
        return self._get() & evaluate(other)

    def __rand__(self, other):
        # if Lazy.full_regime:
        #     return Lazy(lambda: other & self._get())
        # else:
        if isinstance(other, OperatorSection):
            return NotImplemented  # delegate to OperatorSection
        if isinstance(other, Func):
            return other & func(self)
        if isinstance(other, Lazy):
            return Lazy(lambda: other._get() & self._get())  # apply (other & _) under self
        return evaluate(other) & self._get()

    def __getitem__(self, item):
        """Subscription triggers evaluation.

        Assumption: type A is subscriptable
        """
        # if Lazy.full_regime:
        #     return Lazy(lambda: self._get()[item])
        # else:
        if not hasattr(self._get(), '__getitem__'):
            raise TypeError(f"value in {self!r} is not indexable")
        return self.value[item]

    # TODO: support other operators that automatically evaluate: __eq__, etc.


type IterLazy[A] = A | Lazy[IterLazy[A]]  # for use in case of Tail Call Elimination
# Note: A must not be Lazy


@func
def evaluate[A](v: IterLazy[A]) -> A:
    """Evaluate `v`.
    """
    if isinstance(v, Lazy):
        return v._get()
    else:
        return v


def lazy[A, B](expr: Callable[[A], B] | str) -> Func[A, Lazy[B]] | Lazy[Any]:
    """Make `expr` lazy.

    If `expr` is callable, then `lazy(expr)(a)` is equivalent to `Lazy(lambda: expr(a))`.
    TODO: split into separate functions?
    """
    if callable(expr):
        return Func(lambda arg: Lazy(lambda: expr(arg), name=f"`{expr}.{utils.show_args((arg,))}`"))
    else:  # string
        return Lazy(la(f": {expr}", up=2), name=f"`{expr}`")


def lazyf[X, Y](f: Func[X, Y]) -> Func[Lazy[X], Lazy[Y]]:
    """Apply `Lazy` as functor to `f`.
    That is, return a function that applies `f` inside Lazy.
    """
    return Func(lambda x: Lazy(lambda: f(x._get())))


@func
def fpower_lazy[A](f: Func[A, A], n: int) -> Func[A, A]:
    """Lazy version of :func:`FuPy.basic.fpower`.

    When is this useful?  E.g. when `f` does not depend on its argument (is a constant function).
    """
    return id_ if n == 0 else la('x: f(lazy(fpower_lazy(f, n - 1))(x))').rename(f"{f} ⚬ {f}^{n - 1}")


@func
def fpower_left_lazy[A](f: Func[A, A], n: int) -> Func[A, A]:
    """Version of :func:`FuPy.basics.fpower_left` using laziness
    for Tail-Call Elimination.
    """
    @func
    def go(n: int) -> Func[A, A]:
        return id_ if n == 0 else Func(lambda x: Lazy(lambda: (go(n - 1) @ f)(x)), name=f"go({n - 1}) ⚬ {f.show('⚬')}", top='⚬')

    return Func(evaluate @ go(n), name=f"{f.show('^')}^{n}", top='^')

