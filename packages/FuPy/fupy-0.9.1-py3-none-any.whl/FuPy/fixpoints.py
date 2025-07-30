"""
Definitions to support various fixpoints, both on the value level and the type level.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from dataclasses import dataclass
from typing import Final, Protocol

from . import utils
from .basics import *
from .laziness import *

__all__ = [
    "fix",
    "Functor", "fmap", "Fmap",
    "Fix", "in_", "out",
    "F_Algebra", "cata", "cata_",
    "F_CoAlgebra", "ana", "ana_",
    "hylo"
]


@func
def fix[A](f: Func[A, A]) -> A:
    """Return fixpoint of `f`.

    Uses laziness to avoid infinite recursion.
    The call `fix(f)` will result in `f(Lazy(lambda: fix(f)))`.
    Thus, the argument of `f` is made lazy.  TODO: Why "make fix lazy"?  Terminology needs reconsideration.
    """
    # return f(Lazy(lambda: fix(f)))
    return f(lazy(fix)(f))


class Functor[X](Protocol):
    """Type class for functors.

    Deprecated (for use with (co)inductive types).
    """
    def __fmap__[Y](self, f: Func[X, Y]) -> "Functor[Y]":
        """Apply `f` inside self.
        """


@func
def fmap[F, X, Y](f: Func[X, Y]) -> "Func[F[X], F[Y]]":
    """Apply functor `F` to function `f` in `X -> Y` to get function in `F[X] -> F[Y]`.

    Deprecated (for use with (co)inductive types).
    """
    @func(name=f"fmap({f})")
    def fmf(fx: "F[X]") -> "F[Y]":
        """Define `F(f)`.
        """
        return fx.__fmap__(f)

    return fmf


# How a functor operates on functions
type Fmap[F, X, Y] = Func[ Func[X, Y], Func[F[X], F[Y]] ]


# type Iter[F: Functor, A] = A | F[Iter[F, A]]  # not accepted


# TODO: Fix is a Functor (though not defined as implementing the Functor protocol)
# TODO: F does not have to be a Functor, when fmap is provided separately
@dataclass
class Fix[F: Functor]:
    """`Fix[F]` is fixpoint data type for functor `F`.

    For a lazy `Fix`, invoke as `Fix(Lazy(lambda: v))`.
    An alternative would be to define locally:

    .. code-block:: python

        class LazyFix[F, X](Fix[F[X]]):
            def unFix(self) -> F[Fix[F]]:
                return v

        ... LazyFix(None) ...

    """
    _unFix: "Final[F[Fix[F]] | Lazy[F[Fix[F]]]]"

    def __str__(self) -> str:
        return f"Fix.{utils.show_args((self._unFix,))}"

    def __force__(self) -> "Fix[F]":
        self._unFix = utils.force(self._unFix)
        return self

    def unFix(self) -> "F[Fix[F]]":
        # return evaluate(self._unFix)  # TODO: why is evaluate needed?
        return self._unFix

    def __fmap__[G](self, f: Func[F, G]) -> "Func[Fix[F], Fix[G]]":
        return Fix(f(self.unFix()))


@func(name="in")
def in_[F: Functor](a: "F[Fix[F]]") -> Fix[F]:
    """Initial constructor F-algebra of `Fix[F]`.

    Deprecated type bound Functor.
    """
    return Fix(a)


@func
def out[F: Functor](a: Fix[F] | Lazy[Fix[F]]) -> "F[Fix[F]]":
    """Final deconstructor F-coalgebra of `Fix[F]`.

    Inverse of in.
    Deprecated type bound Functor.
    """
    return evaluate(a).unFix()  # TODO: why is evaluate needed?  Lazy does not have unFix


type F_Algebra[F: Functor, X] = Func[F[X], X]
# Deprecated type bound Functor.


@func(name="⦇ … ⦈_F")
def cata[F, X, Y](fmap: Fmap[F, X, Y]
                  ) -> "Func[F_Algebra[F, Y], Func[Fix[F], Y]]":
    """Construct catamorphism given functor and F-algebra (curried).

    cata(fmap: (X -> Y) -> F[X] -> F[Y])(alg: F[Y] -> Y)(x: Fix[F]) -> Y:
        return (alg @ fmap(cata(fmap)(alg)) @ out)(x)

    Note the typing:
    cata(fmap)(alg): Y <- Fix[F]
    out: F[Fix[F]] <- Fix[F]
    fmap(cata(fmap)(alg)): F[Y] <- F[Fix[F]]
    alg: Y <- F[Y]
    """
    # return Func(lambda alg: (fix(Func(lambda rec: alg @ fmap(rec) @ out))
    return Func(lambda alg: (fix(la('rec: alg @ fmap(rec) @ out'))
                             ).rename(f"⦇ {alg} ⦈_{fmap}"),
                name=f"⦇ … ⦈_{fmap}")

    # alternative definition (that doesn't print as nicely)
    # def aux(alg: F_Algebra[F, Y]) -> "Func[Fix[F], Y]":
    #     def rec(x: Fix[F]) -> Y:
    #         return alg(fmap(rec)(out(x)))
    #
    #     return rec
    #
    # return aux



@func(name="⦇ … ⦈")
def cata_[F: Functor, X](alg: F_Algebra[F, X]) -> Func[Fix[F], X]:
    """For F-algebra `alg`, construct catamorphism in `Fix[F] -> X`.

    Deprecated. ?
    """
    # return fix(Func(lambda rec: alg @ fmap(rec) @ out))  # efficiency?
    @func(name=f"⦇ {alg} ⦈")
    def rec(a: Fix[F]) -> X:
        """rec = alg o F.rec o out"""
        return alg(fmap(rec)(out(a)))
        # return (alg @ fmap(rec) @ out)(a)  # less efficient?

    return rec


type F_CoAlgebra[F: Functor, X] = Func[X, F[X]]
# Deprecated type bound Functor.


@func(name="〖 … 〗_F")
def ana[F, X, Y](fmap: Fmap[F, X, Y]
                 ) -> "Func[F_CoAlgebra[F, X], Func[X, Fix[F]]]":
    """Construct anamorphism given functor and F-coalgebra (curried).

    ana(fmap: (X -> Y) -> F[X] -> F[Y])(coalg: Y -> F[Y])(x: X) -> Fix[F]:
        return (in @ fmap(ana(fmap)(coalg)) @ coalg)(x)

    Note the typing:
    ana(fmap)(coalg): Fix[F] <- X
    coalg: F[X] <- X
    fmap(ana(fmap)(coalg)): F[Fix[F]] <- F[X]
    in: Fix[F] <- F[Fix[F]]
    """
    return Func(lambda coalg: (fix(la('rec: in_ @ fmap(rec) @ coalg'))
                               ).rename(f"〖 {coalg} 〗_{fmap}"),
                name=f"〖 … 〗_{fmap}")

    # alternative definition (that doesn't print as nicely)
    # def aux(coalg: F_CoAlgebra[F, X]) -> "Func[X, Fix[F]]":
    #     def rec(x: X) -> Fix[F]:
    #         return in_(fmap(rec)(coalg(x)))
    #
    #     return rec
    #
    # return aux


@func(name="〖 … 〗")
def ana_[F: Functor, X](coalg: F_CoAlgebra[F, X]) -> Func[X, Fix[F]]:
    """For F-coalgebra `coalg`, construct anamorphism in `X -> Fix[F]`.

    Deprecated. ?
    """
    # return fix(Func(lambda rec: in_ @ fmap(lazy(rec)) @ coalg))
    @func(name=f"〖 {coalg} 〗")
    def rec(x: X) -> Fix[F]:
        """rec = in o F.rec o coalg"""
        return in_(fmap(rec)(coalg(x)))
        # return (in_ @ fmap(rec) @ coalg)(x)  # less efficient

    return rec


@func(name="⦇ … ⦈_F ⚬〖 … 〗_F")
def hylo[F, X, Y](fmap: Fmap[F, X, Y]
                  ) -> "Func[Both[F_Algebra[F, Y], F_CoAlgebra[F, X]], Func[X, Y]]":
    """Construct hylomorphism given functor and F-(co)algebras (curried).
    """
    return Func(lambda alg, coalg: (fix(la('rec: alg @ fmap(rec) @ coalg'))
                                    ).rename(f"⦇ {alg}, {coalg} 〗_{fmap}"),
                name=f"hylo_{fmap}")
