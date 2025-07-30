"""
Definitions of basic functions for natural numbers and (potentially infinite) lists.

Copyright (c) 2024 - Eindhoven University of Technology, The Netherlands

This software is made available under the terms of the MIT License.
"""
from typing import Any, Final
from .core import *

_ = x_  # even shorter name for the dummy argument


__all__ = [
    "swap", "coswap", "assoc_left", "assoc_right", "coassoc_left", "coassoc_right",
    "is_left", "untag", "dup",
    "dist_left", "undist_left", "dist_right", "undist_right",
    "Maybe", "nothing", "just", "maybeF",
    "NatF", "natF", "Nat",
    "zero", "succ", "one",
    "NatF_Algebra", "NatF_CoAlgebra",
    "cataNat", "anaNat",
    "is_zero", "pred", "eqNat", "less",
    "intNat", "nat",
    "add", "mul", "sub", "div", "infNat",
    "in_nat", "out_nat", "cata_nat", "ana_nat",
    # "infinite",
    "ListF", "listF", "List_",
    "nil", "cons",
    "ListF_Alg", "ListF_CoAlg",
    "cataList", "anaList",
    "null", "head_tail", "head", "tail",
    "eqList",
    "strList", "listList", "list_",
    "length", "length_nat", "cat",
    "map_", "filter_",
    "concat",
    "take_drop", "take", "drop",
    "unzip", "zip", "zip_with",
    "from_",
    "null_", "cons_", "head_", "tail_",
    "in_list", "out_list", "cata_list", "ana_list",
]


# type: Func[Both[A, B], Both[B, A]]
swap = (second & first).rename("swap")

# type: Func[Either[A, B], Either[B, A]]
coswap = (right | left).rename("coswap")

# type: Func[Both[A, Both[B, C]], Both[Both[A, B], C]]
assoc_left = ((id_ * first) & second @ second).rename("assoc_left")  # (a, (b, c)) -> ((a, b), c)

# type: Func[Both[Both[A, B], C], Both[A, Both[B, C]]]
assoc_right = (first @ first & (second * id_)).rename("assoc_right")  # ((a, b), c) -> (a, (b, c))

# type: Func[Either[A, Either[B, C]], Either[Either[A, B], C]]
coassoc_left = (left @ left | (right + id_)).rename("coassoc_left")  # (a | (b | c)) -> ((a | b) | c)

# type: Func[Either[Either[A, B], C], Either[A, Either[B, C]]]
coassoc_right = ((id_ + left) | right @ right).rename("coassoc_right")  # ((a | b) | c) -> (a | (b | c))

# type: Func[Either[A, B], bool]
is_left = (const(True) | const(False)).rename("is_left")

# type: Func[Either[A, A], A]
untag = (id_ | id_).rename("untag").doc("Take off injection.")

# type: Func[A, Both[A, A]]
dup = (id_ & id_).rename("dup").doc("Construct tuple with duplicated argument.")

# type: Func[Both[A, Either[B, C]], Either[Both[A, B], Both[A, C]]]
dist_left = (((id_ * untag) + (id_ * untag)) @ guard(is_left @ second)).rename("dist_left")

# type: Func[Either[Both[A, B], Both[A, C]], Both[A, Either[B, C]]]
undist_left = ((first & (left @ second)) | (first & (right @ second))).rename("undist_left")
# undist_left = ((first | first) & ((left @ second) | (right @ second))).rename("undist_left")

# type: Func[Both[Either[A, B], C], Either[Both[A, C], Both[B, C]]]
dist_right = (((untag * id_) + (untag * id_)) @ guard(is_left @ first)).rename("dist_right")

# type: Func[Either[Both[A, C], Both[B, C]], Both[Either[A, B], C]]
undist_right = (((left @ first) & second) | ((right @ first) & second)).rename("undist_right")
# undist_left = (((left @ first) | (right @ first)) & (second | second)).rename("undist_right")

type Maybe[X] = Either[Unit, X]  # 1 + X

nothing: Maybe[Any] = left(unit)  # inject left in Maybe[A]


@func
def just[A](a: A) -> Maybe[A]:
    """Inject right into Maybe[A]
    """
    return right(a)


@func
def maybeF[X, Y](f: Func[X, Y]) -> Func[Maybe[X], Maybe[Y]]:
    """Map f over a Maybe value.
    """
    return id_ + f


# (co)inductive type of natural numbers

# Functor for type of natural numbers: how it operates on types
type NatF[X] = Maybe[X]  # 1 + X


@func
def natF[X, Y](f: Func[X, Y]) -> Func[NatF[X], NatF[Y]]:
    """Functor for type of natural numbers: how it operates on functions.
    """
    return id_ + f  # maybeF(f)

# alternatives
# natF = maybe
# natF = (id_ + _).define_as("natF")

# Alternative, defining NatF as instance of Functor
# @dataclass
# class NatF_[X](Functor[X]):
#     unNatF: Maybe[X]
#
#     @override
#     def __fmap__[Y](self, f: Func[X, Y]) -> "Functor[Y]":
#         return maybeF(f)
#         return id_ + f  # natF(f), but the latter would add another indirection

# TODO: How to make a dataclass an instance of a protocol, afterwards?
# i.e., implement the required operations


# @func  # used in cataNat_
# def unNatF_[X](nfx: NatF_[X]) -> Maybe[X]:
#     return nfx.unNatF


type Nat = Fix[NatF]
# type Nat_ = Fix[NatF_]


zero: Final[Nat] = in_(left(unit))


@func
def succ(n: Nat) -> Nat:
    return in_(right(n))


one: Final[Nat] = succ(zero)


type NatF_Algebra[X] = F_Algebra[NatF, X]
type NatF_CoAlgebra[X] = F_CoAlgebra[NatF, X]


# TODO: Why not just define cataNat = cata(natF)?
@func(name=f"⦇ … ⦈_ℕ")
def cataNat[X](alg: NatF_Algebra[X]) -> Func[Nat, X]:
    """Catamorphism from NatF-algebra.
    """
    # return cata(natF)(alg)
    return cata(natF)(alg).rename(f"⦇ {alg} ⦈_ℕ")


# TODO: Why not just define cataNat_ = cata_ @ (_ @ unNatF_)?
# @func(name=f"⦇ … ⦈_ℕ_")
# def cataNat_[X](alg: F_Algebra[NatF_, X]) -> Func[Nat, X]:
#     """Catamorphism from NatF-algebra.
#     """
#     return cata_(alg @ unNatF_).rename(f"⦇ {alg} ⦈_ℕ_")


# TODO: Why not just define anaNat = ana(natF)?
@func(name=f"〖 … 〗_ℕ")
def anaNat[X](coalg: NatF_CoAlgebra[X]) -> Func[X, Nat]:
    """Anamorphism from NatF-coalgebra.
    """
    return ana(natF)(coalg).rename(f"〖 {coalg} 〗_ℕ")


# TODO: Why not just define anaNat_ = ana_ @ (NatF_ @ _)?
# @func(name=f"〖 … 〗_ℕ_")
# def anaNat_[X](coalg: F_CoAlgebra[X, NatF_]) -> Func[X, Nat]:
#     """Anamorphism from NatF-coalgebra.
#     """
#     return ana_(NatF_ @ coalg).rename(f"〖 {coalg} 〗_ℕ_")


# type: Func[Nat, bool]
# is_zero = (( const(True) | const(False) ) @ out).rename("is_zero")
is_zero = cataNat( const(True) | const(False) ).rename("is_zero")

# type: Func[Nat, Nat]  # partial function
pred = (( undefined | id_ ) @ out).rename("pred")
# tuple with identity
# pred = first @ cataNat( const(undefined, 0) | second & succ )

# type: Func[Nat, Func[Nat, bool]]
eqNat = cataNat( const(is_zero) | Func(lambda eq_n: (const(False) | eq_n @ pred) @ guard(is_zero)) ).rename("eqNat")
less = cataNat( const(op.not_ @ is_zero) | Func(lambda less_n: (const(False) | less_n @ pred) @ guard(is_zero)) ).rename("less")

# convert Nat to int

# type: Func[Nat, int]
intNat = cataNat( const(0) | (_ + 1) ).rename("intNat")

# convert int >= 0 to Nat
# type: Func[int, Nat]
nat = anaNat( (const(unit) + (_ - 1)) @ guard(_ == 0) ).rename("nat")

#  various (curried) binary operators on Nat
# type: Func[Nat, Func[Nat, Nat]]
add = Func(lambda m: cataNat( const(m) | succ ), name="add")
mul = Func(lambda m: cataNat( const(zero) | add(m) ), name="mul")
sub = Func(lambda m: cataNat( const(m) | pred ), name="sub")
# div = Func(lambda m: Func(lambda n: anaNat( ( const(unit) + flip(sub)(n) ) @ guard(flip(less)(n)) )(m)),
#            name="div")
div = flip(Func(lambda n: anaNat( ( const(unit) + flip(sub)(n) ) @ guard(flip(less)(n)) ))).rename("div")

# infinite: Final[Nat] = div(one)(zero)
# infNat = anaNat( right )(unit)  # = anaNat( (const(unit) + id) @ guard(const(False)) )(unit)
# infNat = nat(-1)
infNat = fix(succ)

# (co)inductive nat type based on native int

# TODO: use these in intNat and nat (?)
in_nat = (const(0) | (_ + 1)).rename("in_nat")
out_nat = ((const(unit) + (_ - 1)) @ guard((_ == 0))).rename("out_nat")


@func
def cata_nat[X](alg: Func[NatF[X], X]) -> Func[int, X]:
    return fix(Func(lambda rec: alg @ natF(lazy(rec)) @ out_nat)).rename(f"⦇ {alg} ⦈_nat")
    # def rec(n: nat) -> X
    #     return (alg @ (id_ + lazy(rec)) @ out_nat)(n)
    #            alg(((const(unit) + lazy(rec) @ (_ - 1)) @ guard((_ == 0))))
    #            alg(left(unit)) if n == 0 else alg(right(lazy(rec)(n - 1)))
    #            alg(left(unit)) if n == 0 else alg(right(Lazy(lambda: rec(n - 1))))
    #            # assume alg = const(b) | g
    #            b if n == 0 else g(Lazy(lambda: rec(n - 1)))


@func
def ana_nat[X](coalg: Func[X, NatF[X]]) -> Func[X, int]:
    return fix(Func(lambda rec: in_nat @ natF(lazy(rec)) @ coalg)).rename(f"〖 {coalg} 〗_nat")


# (co)inductive list type

type ListF[X] = Either[Unit, Both[Any, X]]  # 1 + A x X


@func
def listF[X, Y](f: Func[X, Y]) -> Func[ListF[X], ListF[Y]]:
    """Functor for list type.
    """
    return id_ + id_ * f

# Alternatives
# listF = ((id_ + _) @ (id_ * +)).define_as("listF")
# listF = (id_ + id_ + _).define_as("listF")

type List_ = Fix[ListF]


nil: Final[List_] = in_(left(unit))


@func
def cons(x: Any, xs: List_) -> List_:
    """Uncurried operator to combine head and tail.
    """
    return in_(right(x, xs))


type ListF_Alg[X] = F_Algebra[ListF, X]
type ListF_CoAlg[X] = F_CoAlgebra[ListF, X]


@func
def cataList[X](alg: ListF_Alg[X]) -> Func[List_, X]:
    """Catamorphism from ListF-algebra.
    """
    return cata(listF)(alg).rename(f"⦇ {alg} ⦈_𝕃")


@func
def anaList[X](coalg: ListF_CoAlg[X]) -> Func[X, List_]:
    """Anamorphism from ListF-algebra.
    """
    return ana(listF)(coalg).rename(f"〖 {coalg} 〗_𝕃")


# type: Func[List_, bool]
null = cataList( is_left ).rename("null")
# null = is_left @ out

# type: Func[List_, Any]
head_tail = (( undefined | id_ ) @ out).rename("head_tail")

# type: Func[List_, Any]
head = (first @ head_tail).rename("head")

# type: Func[List_, List_]
tail = (second @ head_tail).rename("tail")

# check whether two List_'s are equal (curried)
# type: Func[List_, Func[List_, bool]]
eqList = cataList( const(null)
                 | Func(lambda x, r:  # r = eqList(xs)
                              ( const(False)
                              | op.land @ (Func(lambda y: x == y) * r) @ head_tail
                              ) @ guard(null))
                 )

# represent a List_ as a string (fully evaluates)
# type: Func[List_, str]
strList = cataList(const("[]") | Func(lambda x, xs: f"{evaluate(x)} ⊢ {evaluate(xs)}"))

# convert a List_ to a regular Python list (only works if the argument is finite)
# type: Func[List_, list]
listList = cataList(const([]) | Func(lambda x, xs: [evaluate(x)] + evaluate(xs)))

# convert regular Python list to a List_
# type: Func[list, List_]
list_ = anaList( (const(unit) + (Func(lambda xs: xs[0]) & Func(lambda xs: xs[1:]))) @ guard(op.not_) )

length = cataList(const(zero) | succ @ second).rename("length")
length_nat = cataList(const(0) | (1 + _) @ second).rename("length_nat")


@func
def cat(xs: List_, ys: List_) -> List_:
    """Uncurried catenation on List_.
    """
    return cataList( const(ys) | cons )(xs)


# map function over list
# type: Func[Func[X, Y], Func[List_, List_]]
map_ = Func(lambda f: cataList( const(nil) | cons @ (f * id_) ).rename(f"map({f})"),  # TODO: minimize parentheses around f
            name="map")

# filter list by predicate
# type: Func[Func[X, bool], Func[List_, List_]]
filter_ = Func(lambda p: cataList(const(nil) | (cons | second) @ guard(p @ first)).rename(f"filter({p})"),
               name="filter")

concat = cataList( const(nil) | cat ).rename("concat")

take_drop = cata_nat( const(const(nil) & id_) |
                      Func(lambda tdn: (const(nil, nil) | (cons * id_) @ assoc_left @ (id_ * tdn) @ head_tail) @ guard(null))
                      ).rename("take_drop")
take = Func(lambda n: first @ take_drop(n)).rename("take")
drop = Func(lambda n: second @ take_drop(n)).rename("drop")
# drop = cata_nat( const(id_) | (lambda r: (const(nil) | r @ tail) @ guard(null))
#                  ).rename("drop")
# take = cata_nat( const(const(nil)) | (lambda r: (const(nil) | cons @ (id_ * r) @ head_tail) @ guard(null))
#                  ).rename(f"take")

# type: Func[List_[Both[A, B]], Both[List_[A], List_[B]]]
unzip = cataList(const(nil, nil) | Func(lambda xy, ts: (cons(first(xy), first(ts)), cons(second(xy), second(ts))))).rename("unzip")
# type: Func[Both[List_[A], List[B]], List_[Both[A, B]]]
zip = anaList( (const(unit) + ((head * head) & (tail * tail))) @ guard(op.lor @ (null * null)) ).define_as("zip")
# type: Func[Func[Both[A, B], C], Func[Both[List_[A], List[B]], List_[C]]]
zip_with = Func(lambda bop: anaList( (const(unit) + ((bop @ (head * head)) & (tail * tail))) @ guard(op.lor @ (null * null)) )
                ).rename("zip_with")

# type: Func[int, List_[int]]
from_ = anaList( right @ (id_ & (_ + 1)) ).rename("from")

# (co)inductive list_ type based on native list (as snoc lists)

null_ = la('xs: not xs').rename("null_")
cons_ = la('(x, xs): [evaluate(x)] + xs').rename("cons_")
head_ = la('xs: xs[0]').rename("head_")
tail_ = la('xs: xs[1:]').rename("tail_")
in_list = (const([]) | cons_).rename("in_list")
out_list = ((const(unit) + (head_ & tail_)) @ guard(null_)).rename("out_list")


@func
def cata_list[X](alg: Func[ListF[X], X]) -> Func[list, X]:
    # return fix(Func(lambda rec: alg @ listF(rec) @ out_list)).rename(f"⦇ {alg} ⦈_list")
    return fix(la('rec: alg @ listF(rec) @ out_list')).define_as(f"⦇ {alg} ⦈_list")


@func
def ana_list[X](coalg: Func[X, ListF[X]]) -> Func[X, list]:
    return fix(Func(lambda rec: in_list @ listF(rec) @ coalg)).define_as(f"〖 {coalg} 〗_list")
