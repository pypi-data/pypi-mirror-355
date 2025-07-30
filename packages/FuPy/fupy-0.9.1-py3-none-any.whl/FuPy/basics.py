"""
Definitions to support functional programming in Python.
Especially aimed at educational use and not at industrial application.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
import collections.abc as abc
import inspect
from dataclasses import dataclass
from functools import update_wrapper, wraps
from typing import Any, Final, Optional, Callable, Protocol, override

from . import utils
from . import tracing as tr
from .tracing_basics import *

__all__ = [
    "Empty", "Unit", "unit",
    "Either", "Both",
    "Func", "func", "la",
    "undefined",
    "id_", "const", "left", "right", "guard", "first", "second",
    "curry", "uncurry", "flip", "ap",
    "compose", "split", "case_", "ftimes", "fplus", "fpower",
    "fpower_left",
    "fexp",
    "x_",
]


class Empty:
    """The Empty type, without any values.
    """
    def __new__(cls, *args, **kwargs):
        raise TypeError("Empty cannot be instantiated")


class Unit:
    """The Unit type 𝟙 with only the unit value.

    A singleton class.
    """
    _has_instance = False

    def __init__(self) -> None:
        """Enforce singleton.
        """
        if Unit._has_instance:
            raise RuntimeError("Unit is a singleton class; use `unit` instead")
        Unit._has_instance = True

    @override
    def __repr__(self) -> str:
        return "unit"

    @override
    def __str__(self) -> str:
        return "_"  # 2IPH0 Math notation

    def __len__(self) -> int:
        return 0

    def __iter__(self):
        """Makes unit unpackable.

        Also see Func.__call__.
        """
        return iter(())


unit: Final[Unit] = Unit()  # the unit value
# We could also have used () as unit value,
# but then we could not type hint it with tuple[]
# Also, then we could not give it a custom str/repr.


@dataclass
class Left[A]:
    """The left option of the sum type Either.
    """
    value: Final[A]

    def __str__(self) -> str:
        return str(f"↪︎.{utils.show_args((self.value,))}")

    def __force__(self) -> "Left[A]":
        self.value = utils.force(self.value)
        return self


@dataclass
class Right[B]:
    """The right option of the sum type Either.
    """
    value: Final[B]

    def __str__(self) -> str:
        return str(f"↩︎.{utils.show_args((self.value,))}")

    def __force__(self) -> "Right[A]":
        self.value = utils.force(self.value)
        return self


# Sum type A + B is Either[A, B]
type Either[A, B] = Left[A] | Right[B]


# Product type A x B is Both[A, B]
type Both[A, B] = tuple[A, B]  # TODO: tuple(Lazy[A], Lazy[B]) ?


class Func[A, B]:
    """Function space type of functions A -> B.

    Supports various operations on such functions:

    - application (`f(arg)`), composition (`f @ g`)
    - split (`f & g`), case (`f | g`)
    - product (`f * g`), sum (`f + g`)
    - exponentiation (`f ** n`)

    These operators can be sectioned.

    It would be nice if this could be incorporated into `types.FunctionType`
    (which is immutable; so, these cannot be added dynamically.)

    Note that in an FP language like Haskell, functions take exactly one argument
    (and return one result).
    That is why we give a `Func` the unit value as default argument.
    There is some tension between this view and the broader view of Python on functions
    (the latter can have no arguments or multiple arguments).
    The Func wrapper handles this by automatically (un)packing of arguments.
    Consider the call `Func(f)(*args)` where `args` is a tuple and
    f is defined as `def f(*fargs): ...` where `fargs` is also a tuple.
    Let `R` be the number of _required_ non-keyword arguments of `f`
    and `A =  len(args)` the number of actual arguments of `Func(f)`.
    The call `Func(f)(*args)` is handled as follows:

    +----------+-------------+---------------------+----------------+
    |          | `A == 0`    | `A == 1`            | `A >= 2`       |
    +==========+=============+=====================+================+
    | `R == 0` | `f(*args)`  | `f(*(args[0])) (a)` | `TypeError`    |
    +----------+-------------+---------------------+----------------+
    | `R == 1` | `f(unit)`   | `f(args[0])`        | `f(args) (b)`  |
    +----------+-------------+---------------------+----------------+
    | `R >= 2` | `TypeError` | `f(*(args[0])) (c)` | `f(*args) (d)` |
    +----------+-------------+---------------------+----------------+

    Notes:

    * (a) `args[0]` must behave like an empty tuple, e.g. `unit`.
    * (b) pack the arguments and pas them as a single tuple.
    * (c) unpack the argument and pass the unpacked values separately;
          N.B. the single argument must be an iterable of appropriate length
    * (d) the number of arguments provided and expected must match.
    * Keyword parameters are passed on.
    """
    COMBINATORS = {'@': '⚬', '&': '△', '|': '▽', '*': '⨯', '+': '+', '**': '^'}
    PRIORITIES = {'': 9, '.': 8, '°': 7, '?': 7, '^': 7, '⚬': 5, '△': 3, '⨯': 3, '▽': 1, '+': 1, 'λ': 0}
    fully_parenthesize = False  # affects self.show()

    def __init__(self, f: Callable[..., B], name: Optional[str] = None,
                 r: Optional[int] = None, top: str = '') -> None:
        """Wrap f in Func.

        * `self.name` is how it prints in Math notation.
        * `self.r` is minimum number of required arguments
          (None means: attempt to determine `r` from `f`, defaulting to 1)
        * `self.top` encodes top-level operator in `f`'s construction,
           in Math notation, used to suppress unneeded surrounding parentheses
        """
        if r is None:
            try:
                r = utils.count_required_args(f)
            except ValueError as e:
                r = 1  # default for functions that cannot be inspected
        self.required_args_count = r
        self.func = f  # semantics
        self.top = top  # top-level operator
        update_wrapper(self, f, updated={})
        self.name = name or (f.__name__ if hasattr(f, '__name__') else str(f))  # syntax

    @override
    def __repr__(self) -> str:
        return f"Func({self}, r={self.required_args_count}, top={self.top!r})"

    @override
    def __str__(self) -> str:
        return self.name

    def __force__(self) -> "Func[A, B]":
        self.func = utils.force(self.func)
        return self

    def show(self, op: str) -> str:
        """Return name in the context of operator `op`, adding parentheses if needed.
        """
        if Func.fully_parenthesize:
            if self.top != '' or op == '':
                return f"({self})"
        if (Func.PRIORITIES[self.top] > Func.PRIORITIES[op] or
            Func.PRIORITIES[self.top] == Func.PRIORITIES[op] == 7
            ):
            return str(self)
        elif self.top == op == '⚬':
            return str(self)
        else:
            return f"({self})"

    def show_top(self) -> str:
        """Show top-level function for motivation of function application step.
        """
        if self.top == '':
            return self.name
        else:
            return self.top

    def rename(self, name: str, top: Optional[str] = '') -> "Func[A, B]":
        """Rename f.
        """
        self.name = name
        self.top = top
        return self

    def define_as(self, name: str) -> "Func[A, B]":
        """Define name as self.
        """
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(self, name=name, top='')

    def doc(self, docstring: str) -> "Func[A, B]":
        """Add docstring to self.
        """
        self.__doc__ = docstring
        return self

    def __call__(self, *args: A, **kwargs) -> B:
        """Apply self to args.
        """
        # TODO: Should keyword arguments be passed as well?
        from .laziness import Lazy
        actual_args_count = len(args)
        # print(f"{self} requires {self.required_args_count} args; provided args: {args}")
        # print(f"call entry: {self.show('^')}{args!r}")
        # Cases to distinguish
        # R = self.required_args_count
        # R == 0 and args == (): treat as unit; new_args = args; show as (unit)
        #        and args == (x,): check that x == unit or x == (); new_args = (); show as args
        #        and args == (x, y, ...): TypeError
        # R == 1 and args == (): new_args = (unit,); show as new_args
        #        and args == (x,): new_args = args; show as either, but when isinstance(x, tuple), show as x
        #        and args == (x, y, ...): new_args = (args,); auto pack; show as args
        # R >= 2 and args == (): TypeError
        #        and args == (x,): new_args = x; auto unpack; show as x
        #        and args == (x, y, ...): new_args = args; show as either
        comment = ""
        if self.required_args_count == 1:  # pass required one argument
            if actual_args_count == 1:  # "normal" 1-from-1: pass on as is
                new_args = args
                if isinstance(args[0], tuple):
                    show_args_as = args[0]  # avoid double parentheses around arguments
                else:
                    show_args_as = args
            elif not actual_args_count:  # the 1-from-0 case
                new_args = (unit,)
                show_args_as = new_args
                comment = "; auto-provide unit argument"
            else:  # 1-from-2+: pass as tuple (auto-pack)
                new_args = (args,)
                show_args_as = args
                comment = "; auto-pack arguments in tuple"
        else:  # f requires zero or more than one argument
            if actual_args_count == 1:  # x-from 1 where x != 1: auto-unpack the 1 argument
                new_args = args[0]  # it must be iterable and of matching length (checked below)
                # What if actual argument is a thunk (Lazy object)?
                if not self.required_args_count:  # 0-from-1: auto convert unit
                    if new_args is not unit and new_args != ():  # ? also allow Lazy?  and later check it for unit value?
                        raise TypeError(f"{self.func!r} requires no argument, but actual argument {new_args!r} is not unit")
                    show_args_as = (unit,)
                    comment = "; auto-provide unit argument"
                else:  # self.required_args_count >= 2
                    if isinstance(new_args, Lazy):
                        old_args = new_args
                        new_args = (Lazy(lambda: first(old_args), name=f"first.{old_args}"),
                                    Lazy(lambda: second(old_args), name=f"second.{old_args}"))
                    if not isinstance(new_args, tuple):
                        raise TypeError(f"{self.func!r} requires {self.required_args_count} arguments, "
                                        f"but actual argument {new_args!r} is not a tuple")
                    show_args_as = new_args
                    comment = "; auto-unpack arguments from tuple"
            else:  # x-from-y where x != 1 and y != 1: pass on as is (numbers must match; checked below)
                new_args = args
                show_args_as = args
        # print(f"  passed args: {new_args}")

        # TODO: in trace step, mention whether evaluation is lazy
        tr.trace_step(lambda: ApplicationStep(f"{self.show('.')}.{utils.show_args(show_args_as)}"))
        tr.trace_step(lambda: MotivationStep(f"def. of {self.show_top()}{comment}"))

        tr.inc_depth()
        actual_args_count = len(new_args)
        if self.required_args_count != actual_args_count:
            raise TypeError(f"{self.func!r} argument mismatch: {self.required_args_count} required, "
                            f"but {actual_args_count} given")
        # TODO: full laziness; but this approach does not work.
        # from FuPy.laziness import Lazy, evaluate
        # if (Lazy.full_regime and
        #         (isinstance(arg, Lazy) for arg in new_args) and
        #         self.show_top() != 'λ' and
        #         self is not evaluate
        #     ):
        #     print("PROPAGATING LAZINESS")
        #     result = Lazy(la(': self.func(*(evaluate(arg) for arg in args), **kwargs)'),
        #                   name=f"(λ: {self.name}{utils.show_args(new_args)})")
        # else:
        result = self.func(*new_args, **kwargs)
        # print(f"  result: {result}")
        # print(f"call exit: {self.show('^')}{new_args!r} ~> {result!r}")
        tr.dec_depth()
        tr.trace_step(lambda: ResultStep(f"{utils.show_value(result)}"))
        return result

    def __matmul__[Z](self, g: "Func[Z, A]") -> "Func[Z, B]":
        """Return self o g.

        If g is not an instance of Func, then it is wrapped as Func.
        The typing is difficult to express:
        * if g expects no or more than one argument,
          then the composition has a single tuple argument.
        """
        if not isinstance(g, Func):
            return NotImplemented
        name = f"{self.show('⚬')} ⚬ {g.show('⚬')}"
        # return Func(lambda z: self(g(z)),
        #             name=f"{self.show('⚬')}{op}{g.show('⚬')}", top='⚬')
        # print(f"constructing {name}")
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda z: self(g(z)), name, top='⚬')
        # return la('z: self(g(z))').rename(name, top='⚬')

    def __rmatmul__[C](self, g: "Func[B, C]") -> "Func[A, C]":
        """Return g o self.
        """
        if not isinstance(g, Func):
            return NotImplemented
        return g @ self

    def __and__[C](self, g: "Func[A, C]") -> "Func[A, Both[B, C]]":
        """Return self split g.
        """
        from .laziness import Lazy

        if not isinstance(g, Func):
            return NotImplemented
        name = f"{self.show('△')} △ {g.show('△')}"
        # print(f"constructing {name}")
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        # return Func(lambda a: LazyTuple(lazy(self)(a), lazy(g)(a)),
        return Func(lambda a: (Lazy(lambda: self(a), name=f"`{self.show('.')}.{utils.show_args((a,))}`"),
                                        Lazy(lambda: g(a), name=f"`{g.show('.')}.{utils.show_args((a,))}`")),
                    name=name, top='△')

    def __rand__[C](self, g: "Func[A, C]") -> "Func[A, Both[C, B]]":
        """Return g split self.
        """
        if not isinstance(g, Func):
            return NotImplemented
        return g & self

    def __or__[Z](self, g: "Func[Z, B]") -> "Func[Either[A, Z], B]":
        """Return self case g.
        """
        from FuPy.laziness import evaluate

        if not isinstance(g, Func):
            return NotImplemented
        name = f"{self.show('▽')} ▽ {g.show('▽')}"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))

        @func(name=name, top="▽")
        def case_(x: Either[A, Z]) -> B:
            match evaluate(x):
                case Left(value=a):
                    return self(a)
                case Right(value=z):
                    return g(z)
                case _:
                    raise TypeError(f"type of argument {x!r} of {name} is neither Left nor Right")

        return case_

    def __ror__[Z](self, g: "Func[Z, B]") -> "Func[Either[Z, A], B]":
        """Return g case self.
        """
        if not isinstance(g, Func):
            return NotImplemented
        return g | self

    def __mul__[C, D](self, g: "Func[C, D]") -> "Func[Both[A, C], Both[B, D]]":
        """Return self x g.
        """
        from .laziness import Lazy

        if not isinstance(g, Func):
            return NotImplemented
        name = f"{self.show('⨯')} ⨯ {g.show('⨯')}"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda a, c: (Lazy(lambda: self(a), name=f"`{self.show('.')}.{utils.show_args((a,))}`"),
                                           Lazy(lambda: g(c), name=f"`{g.show('.')}.{utils.show_args((c,))}`")),
        # return (self @ first) & (g @ second)  # not done this way because it is less efficient
                    name=name, top='⨯')

    def __rmul__[C, D](self, g: "Func[C, D]") -> "Func[Both[C, A], Both[D, B]]":
        """Return g x self.
        """
        if not isinstance(g, Func):
            return NotImplemented
        return g * self

    def __add__[C, D](self, g: "Func[C, D]") -> "Func[Either[A, C], Either[B, D]]":
        """Return self + g.
        """
        from FuPy.laziness import Lazy, evaluate

        if not isinstance(g, Func):
            return NotImplemented
        name = f"{self.show('+')} + {g.show('+')}"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))

        @func(name=name, top="+")
        def fsum_(x: Either[A, C]) -> Either[B, D]:
            match evaluate(x):
                case Left(value=a):
                    return left(Lazy(lambda: self(a), name=f"`{self.show('.')}.{utils.show_args((a,))}`"))
                case Right(value=c):
                    return right(Lazy(lambda: g(c), name=f"`{g.show('.')}.{utils.show_args((c,))}`"))
                case _:
                    raise TypeError(f"type of argument {x!r} of {name} is neither Left nor Right")

        return fsum_
        # return ((left @ self) | (right @ g)).rename(name, top='+')  # would not add laziness

    def __radd__[C, D](self, g: "Func[C, D]") -> "Func[Either[C, A], Either[D, B]]":
        """Return g + self.
        """
        if not isinstance(g, Func):
            return NotImplemented
        return g + self

    def __pow__(self: "Func[A, A]", n: int) -> "Func[A, A]":
        """Repeated composition.
        A.k.a. as function exponentiation.
        Cf.  :func:`FuPy.prelude.cata_nat`.

        Assumptions: `A == B and n >= 0`
        Warning: Only use this with small values of `n`,
        since `f ** n` is fully expanded to `f @ f @ ... @ f` before applying it.
        :func:`fpower_left` evaluates without burdening the stack.
        """
        if not isinstance(n, int) or n < 0:
            return NotImplemented
        if n == 0:
            return id_
        elif n == 1:  # optimization
            return self
        else:
            return (self @ self ** (n - 1)).rename(
                    f"{self.show('^')}^{n}", top='^')
            # N.B. f ** -1 does not terminate
            # We can make f ** -1 = fix(f)
            # return (lazy(self ** _)(n - 1) @ self).rename(f"{self}^{n}")  # fold-left over nat
            # TODO: which is better:  self @ self ** (n - 1)  or  self ** (n - 1) @ self

    def __xor__(self, g: "Func[C, D]") -> "Func[ Func[D, A], Func[C, B] ]":
        """Return self ^ g.
        """
        if not isinstance(g, Func):
            return NotImplemented
        name = f"{self.show('^')} ^ {g.show('^')}"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda h: self @ h @ g, name=name, top="^")

    def __rxor__(self, f: "Func[C, D]") -> "Func[ Func[B, C], Func[A, D] ]":
        """Return f ^ self.
        """
        if not isinstance(f, Func):
            return NotImplemented
        name = f"{f.show('^')} ^ {self.show('^')}"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda h: f @ h @ self)


def func(obj: Optional[Callable] = None, **kwargs) -> Callable:
    """Decorate obj by wrapping it in Func.

    When obj is None, it returns a wrapping function.
    Avoids double wrapping.
    """
    @wraps(func)
    def func_decorator(obj: Callable) -> Callable:
        if isinstance(obj, Func):  # don't decorate again
            return obj
        return Func(obj, **kwargs)

    if obj is None:
        return func_decorator
    else:
        return func_decorator(obj)


def la(la_expr: str, up: int = 1) -> Func[Any, Any]:
    """Define a lambda abstraction with zero or more bound variables.
    Returns a curried or uncurried function wrapped in `Func`.
    Capture local and global variables `up` call stack frames up.

    Argument `la_expr` must have the shape:

        `variables: expr`

    where `variables` is a comma-separated list: `variable, ..., variable`,
    where each `variable` can be
    * empty (no name/tuple)
    * a single name
    * a tuple of zero or more names

    Empty or an empty tuple results in a constant function with `unit` as argument.
    A tuple of 2 or more names results in an uncurried function.
    Multiple variables result in a curried function.

    `la('a, (b, c), , d: (a, b, c, d, e, f)')` where `e == 42` locally and `f` is global,
    results (roughly) in:

    .. code-block:: python

        Func(lambda a:
             Func(lambda b, c:  # this is an uncurried function
                  Func(lambda:  # this is a constant function
                       Func(lambda d: (a, b, c, d, e),
                            name=...),
                       name=...),
                  name=...),
             name=...)

    Recursive approach, with auto capturing of locals.
    """
    # TODO: investigate performance loss, due to parsing and eval
    # from pprint import pprint
    # pprint(f"la_expr: {la_expr}")
    try:
        parameters, body = la_expr.split(':', 1)
    except ValueError:
        raise SyntaxError(f"la({la_expr!r}) has no `:`")
    parameters, body = parameters.strip(), body.strip()
    # param_names = [param.strip().lstrip('()').rstrip(')') for param in parameters.split(',')]
    # find first parameter (could be more robust?)
    if parameters.startswith('('):  # tuple of parameters
        try:
            parameter, rest = parameters.lstrip('(').split(')', 1)  # rest is empty if ')' not present
        except ValueError:
            raise SyntaxError(f"la({la_expr!r}) has `(` without `)`")
        rest = rest.split(',', 1)[1:]
    else:  # single parameter
        parameter, *rest = parameters.split(',', 1)
    # N.B. parameter can be empty
    # len(rest) is 1 or 0, depending on whether there was a comma or not

    parent_frame = inspect.currentframe()
    for i in range(up):
        parent_frame = parent_frame.f_back
    parent_globals = parent_frame.f_globals
    parent_locals = parent_frame.f_locals
    # pprint(f"parent_locals: {parent_locals}")
    try:
        lambda_body = eval(f"lambda: {body}")
    except SyntaxError as excinfo:
        raise SyntaxError(f"la({la_expr!r}) body `{body}`: {excinfo}")
    # pprint(f"names: {lambda_body.__code__.co_names}")
    if parent_locals is parent_globals:
        custom_locals = {}
    else:
        custom_locals = {key: parent_locals[key]
                         for key in lambda_body.__code__.co_names
                         if key in parent_locals}
    # pprint(f"custom_locals: {custom_locals}")
    bindings = '\n'.join(utils.indent_lines(f"{var} = {utils.show_value(value)}", '  ')
                         for var, value in custom_locals.items())
    # pprint(bindings)
    where_clause = f" where {{\n{bindings}\n}}" if bindings else ''  # for use in Func.name (syntax)
    closure = ','.join(f" {var}={var}"
                       for var in custom_locals)
                       # for var in lambda_body.__code__.co_names
                       # if var not in param_names)  # for use in Func.func (semantics)
    # pprint(closure)
    new_body = f"la('{rest[-1].strip()}: {body}')" if rest else body  # TODO: what if body contains quotes?
    la_expr_new = f"lambda{' ' if parameter else ''}{parameter}{',' if closure and parameter else ''}{closure}: {new_body}"
    # pprint(f"la_expr_new: {la_expr_new}")
    name=f'''λ {parameters}: `{body}`{where_clause}'''
    tr.trace_step(lambda: DefinitionStep(f"{name}"))
    try:
        new_func = eval(la_expr_new, parent_globals, custom_locals)
    except SyntaxError as excinfo:
        raise SyntaxError(f"la({la_expr!r}) has bad parameter `{parameter}`: {excinfo}")
    return Func(new_func, name=name, top='λ')


@func(name="⊥", r=1)
def undefined[A](a: A = unit) -> Empty:
    """Abort evaluation.
    Prints as '⊥'.
    """
    raise ValueError(f"undefined({'' if a is unit else repr(a)})")


@func(name="id")
def id_[A](a: A) -> A:
    """Polymorphic identity function.
    Prints as 'id'.
    """
    return a


@func(name="(°)")
def const[A, B](b: B) -> Func[A, B]:
    """Construct the constant function always returning b.
    Prints as '(°)'.
    We use the (superscript) degree symbol as best approximation of a superscript bullet
    (which is not available in Unicode).
    """
    @func(name=f"{b.show('°') if isinstance(b, Func) else utils.show_value(b)}°", top='°')
    def const_b(a: A) -> B:
        """Constant function always returning b.
        """
        return b

    return const_b


@func(name="↪︎")
def left[A, B](a: A) -> Either[A, B]:
    """Inject left into sum type.
    Prints as '↪︎'.
    """
    return Left(a)


@func(name="↩︎")
def right[A, B](b: B) -> Either[A, B]:
    """Inject right into sum type.
    Prints as '↩︎'.
    """
    return Right(b)


@func(name="(?)")
def guard[A](p: Func[A, bool]) -> Func[A, Either[A, A]]:
    """For predicate p, construct function p? in (A -> bool) -> A -> Either[A, A].
    Prints as '(?)'.
    """
    from FuPy.laziness import evaluate
    @func(name=f"{p.show('?')}?", top='?')
    def guard_p(a: A) -> Either[A, A]:
        """Return p?(a).
        """
        if p(evaluate(a)):
            return Left(a)
        else:
            return Right(a)

    return guard_p


@func(name="≪")
def first[A, B](t: Both[A, B]) -> A:
    """Project left out of product type.
    Prints as '≪'.
    """
    from FuPy.laziness import evaluate
    return evaluate(t[0])  # evaluate not really needed


@func(name="≫")
def second[A, B](t: Both[A, B]) -> B:
    """Project right out of product type.
    Prints as '≫'.
    """
    from FuPy.laziness import evaluate
    return evaluate(t[1])  # evaluate not really needed


def _parenth(a: Any) -> str:
    """Parenthesize a if needed.
    """
    if isinstance(a, Func):
        return a.show('^')
    else:
        return a


class OperatorSection:
    """Support for operator sectioning.

    `OperatorSection()` is used as dummy argument to implicitly create lambda expressions.
    It must not implement `__call__`, because otherwise an `OperatorSection` object will not work
    with `Func` function combinators as expected.
    """
    # name: Final[str] = ''
    _has_instance = False

    def __init__(self) -> None:
        """Enforce singleton.
        """
        if OperatorSection._has_instance:
            raise RuntimeError("OperatorSection is a singleton class; use `x_` instead")
        OperatorSection._has_instance = True

    @override
    def __repr__(self) -> str:
        return f"OperatorSection()"

    def __str__(self) -> str:
        """Prints nothing, which is needed when both operands are omitted.
        """
        return ''

    def __eq__(self, other):
        name = f"(={other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x == other, name=name)

    def __ne__(self, other):
        name = f"(≠{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x != other, name=name)

    def __ge__(self, other):
        name = f"(≥{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x >= other, name=name)

    def __gt__(self, other):
        name = f"(>{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x > other, name=name)

    def __le__(self, other):
        name = f"(≤{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x <= other, name=name)

    def __lt__(self, other):
        name = f"(<{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x < other, name=name)

    def __add__(self, other):
        name = f"(+{' ' if callable(other) else ''}{_parenth(other)})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x + other, name=name)
        # return la('x: x + other').rename(name)  # TODO: consider

    def __radd__(self, other):
        name = f"({_parenth(other)}{' ' if callable(other) else ''}+)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other + x, name=name)

    def __sub__(self, other):
        name = f"(-{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x - other, name=name)

    def __rsub__(self, other):
        name = f"({other}-)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other - x, name=name)

    def __mul__(self, other):
        # Naming of `_ * _` cannot be done right, in general.
        # Currently, we use '*' in that case.
        # Keep in mind that OperatorSection is not callable.
        name = f"({'⨯ ' if callable(other) else '*'}{_parenth(other)})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x * other, name=name)

    def __rmul__(self, other):
        name = f"({_parenth(other)}{' ⨯' if callable(other) else '*'})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other * x, name=name)

    def __matmul__(self, other):
        # N.B. other can be OperatorSection or Lazy
        other_os = isinstance(other, OperatorSection)
        if not isinstance(other, (Func, OperatorSection)):
            return NotImplemented
        name = f"({'⚬' if other_os else '⚬ '}{_parenth(other)})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x @ other, name=name)

    def __rmatmul__(self, other):
        if not isinstance(other, Func):
            return NotImplemented
        name = f"({_parenth(other)} ⚬)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other @ x, name=name)

    def __truediv__(self, other):
        name = f"(/{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x / other, name=name)

    def __rtruediv__(self, other):
        name = f"({other}/)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other / x, name=name)

    def __floordiv__(self, other):
        name = f"(div{'' if isinstance(other, OperatorSection) else ' '}{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x // other, name=name)

    def __rfloordiv__(self, other):
        name = f"({other} div)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other // x, name=name)

    def __mod__(self, other):
        name = f"(mod{'' if isinstance(other, OperatorSection) else ' '}{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x % other, name=name)

    def __rmod__(self, other):
        name = f"({other} mod)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other % x, name=name)

    def __pow__(self, other):
        name = f"(**{other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x ** other, name=name)

    def __rpow__(self, other):
        name = f"({other}{'^' if isinstance(other, Func) else '**'})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other ** x, name=name)

    def __and__(self, other):
        # N.B. other can be OperatorSection
        other_os = isinstance(other, OperatorSection)
        if not isinstance(other, (Func, OperatorSection)):
            return NotImplemented
        name = f"({'△' if other_os else '△ '}{_parenth(other)})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x & other, name=name)

    def __rand__(self, other):
        if not isinstance(other, Func):
            return NotImplemented
        name = f"({_parenth(other)} △)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other & x, name=name)

    def __or__(self, other):
        # N.B. other can be OperatorSection
        other_os = isinstance(other, OperatorSection)
        if not isinstance(other, (Func, OperatorSection)):
            return NotImplemented
        name = f"({'▽' if other_os else '▽ '}{_parenth(other)})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: x | other, name=name)

    def __ror__(self, other):
        if not isinstance(other, Func):
            return NotImplemented
        name = f"({_parenth(other)} ▽)"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: other | x, name=name)

    def __divmod__(self, other):
        name = f"divmod( , {other})"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: divmod(x, other), name=name)

    def __rdivmod__(self, other):
        name = f"divmod({other}, )"
        tr.trace_step(lambda: DefinitionStep(f"{name}"))
        return Func(lambda x: divmod(other, x), name=name)


# object.__lshift__(self, other)
# object.__rshift__(self, other)
# object.__xor__(self, other)
#
# object.__rlshift__(self, other)
# object.__rrshift__(self, other)
# object.__rxor__(self, other)


# Client code may want to define `_ = x_` to simplify operator section notation.
# This is not done here, because `_` has a special meaning in some REPLs.
x_ = OperatorSection()


@func
def curry[A, B, C](f: "Func[Both[A, B], C]") -> "Func[A, Func[B, C]]":
    """Curry `f`.
    """
    return Func(lambda a: Func(lambda b: f(a, b),
                               name=f"curry.{f.show('.')}.({utils.show_args((a,))})"),
                name=f"curry.{f.show('.')}")


@func
def uncurry[A, B, C](f: Func[A, Func[B, C]]) -> Func[Both[A, B], C]:
    """Uncurry `f`.
    """
    return Func(lambda t: f(first(t))(second(t)),
                name=f"uncurry.{f.show('.')}")


@func
def flip[A, B, C](f: Func[A, Func[B, C]]) -> Func[B, Func[A, C]]:
    """Flip `f`:  swap arguments on curried function `f`.
    """
    return Func(lambda b: Func(lambda a: f(a)(b), name=f"flip.{f.show('.')}.({utils.show_args((b,))})"), name=f"flip.{f.show('.')}")


# function operators as uncurried functions
# note that these operators are also available via FuPy.operator
# under different names: call, matmul, and_, or_, mul, add, pow

@func
def  ap[A, B](f: Func[A, B], x: A) -> B:
    """Function application as uncurried operator.
    """
    return f(x)

@func
def compose[A, B, C](f: Func[B, C], g: Func[A, B]) -> Func[A, C]:
    """Function composition as uncurried operator.
    """
    return f @ g

@func
def split[A, B, C](f: Func[A, B], g: Func[A, C]) -> Func[A, Both[B, C]]:
    """Function split as uncurried operator.
    """
    return f & g
    # split = la('(f, g): f & g').rename("split")


@func(name="case")
def case_[A, B, C](f: Func[A, C], g: Func[B, C]) -> Func[Either[A, B], C]:
    """Function case as uncurried operator.
    Prints as 'case'.
    """
    return f | g


@func
def ftimes[A, B, C, D](f: Func[A, C], g: Func[B, D]) -> Func[Both[A, B], Both[C, D]]:
    """Functorial product as uncurried operator.
    """
    return f * g


@func
def fplus[A, B, C, D](f: Func[A, C], g: Func[B, D]) -> Func[Either[A, B], Either[C, D]]:
    """Functorial sum as uncurried operator.
    """
    return f + g


@func
def fpower[A](f: Func[A, A], n: int) -> Func[A, A]:
    """Repeated function composition.
    This is fold(-right) over nat.
    Also see :func:`FuPy.prelude.cata_nat`.

    Assumption: n >= 0
    """
    return f ** n


@func
def fpower_left[A](f: Func[A, A], n: int) -> Func[A, A]:
    """Repeated function composition.
    This is like fold-left over nat.
    It is tail recursive and was turned into a loop.

    Assumption: n >= 0
    """
    @func(name=f"{f.show('^')}^{n}", top='^')
    def fpl(x: A) -> A:
        result = x

        for i in range(n):
            result = f(result)

        return result

    return fpl


@func
def fexp[A, B, C, D](f: Func[A, B], g: Func[C, D]) -> Func[C, B]:
    """Functorial exponentiation as uncurried operator.
    """
    return f ^ g


