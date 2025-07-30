<img src="https://gitlab.tue.nl/t-verhoeff-software/fupy/-/raw/main/images/FuPy.png" alt="FuPy logo" style="float: right; margin-left: 20px; margin-bottom: 20px;">

# FuPy: Functional Programming in Python, for Education

[![Pipeline Status](https://gitlab.tue.nl/t-verhoeff-software/fupy/badges/main/pipeline.svg)](https://gitlab.tue.nl/t-verhoeff-software/fupy/pipelines)
[![Test Coverage](https://gitlab.tue.nl/t-verhoeff-software/fupy/badges/main/coverage.svg)](https://gitlab.tue.nl/t-verhoeff-software/fupy/-/commits/main)
[![Latest Release](https://gitlab.tue.nl/t-verhoeff-software/fupy/-/badges/release.svg)](https://gitlab.tue.nl/t-verhoeff-software/fupy/-/releases)[![PyPI version](https://badge.fury.io/py/FuPy.svg)](https://badge.fury.io/py/FuPy)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](https://gitlab.tue.nl/t-verhoeff-software/fupy/-/blob/main/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/fupy/badge/?version=latest)](https://fupy.readthedocs.io/en/latest/?badge=latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/FuPy.svg)](https://pypi.org/project/FuPy/)

## Overview

* [Documentation](https://fupy.readthedocs.io/en/latest/)
* For some examples, see [demo.py](https://gitlab.tue.nl/t-verhoeff-software/fupy/-/raw/main/examples/demo.py).

Python offers (limited) support for functional programming:
* functions are first-class citizens;
* functions can take functions as arguments and can return functions
* lambda expressions for anonymous functions

`FuPy` aims to overcome some limitations, by adding:
* basic types and type constructors
  - `Empty` type without values
  - `Unit` type with value `unit`
  - `Either[A, B]` (disjoint sum) type
  - `Both[A, B]` (product) type (tuple)
  - `Func[A, B]` function space type
* function composition and other function combinators
  - `@` for head-to-tail composition, also written as ⚬
  - `&` for split, also written as △
  - `|` for case, also written as ▽
  - `*` for product (functor over product/tuple type), also written as ⨯
  * `+` for sum (functor over sum/Either type), also written as +
  * `**` for iterated composition, also written with a superscript
  * `^` for functorial exponentiation
* auto (un)packing of arguments in case of functions with no/multiple arguments
* predefined common functions:
  - `id_`, `const`, `left`, `right`, `guard`, `first`, `second`
  - `curry`, `uncurry`, `flip`, `ap`,
  - `compose`, `split`, `case_`, `fplus`, `ftimes`, `fpower`, `fpower_left`
* [operator sections](https://wiki.haskell.org/Section_of_an_infix_operator)
* lazy expressions (suspended computations)
* printable function and lambda expressions
* evaluation tracing
* inductive and co-inductive types
  - `Functor`, `fmap`
  - `Fix`, `fix`
  - `cata` (catamorphisms, folds)
  - `ana` (anamorphims, unfolds)

Main classes:
* `Func`, for composable, printable, and traceable functions with auto-(un)packing of arguments.
* `OperatorSection`, for operator sections
* `Lazy`, for lazy expressions.

Not intended for industrial use:
* there are performance penalties in terms of memory and execution overhead

Notes:
* Type hints do not all verify (but it works).
  The Python type system is too limited
  (we need Higher-Kinded Types, HKTs).
* Binding strength of function combinators are as applied by Python,
  doesn't correspond to the theory.

## Future work
* Applicatives and monads

## Installation

``` shell
pip install FuPy
```

## Development (for developers)

* Build:
  ```shell
  python -m build
  ```
* Test:
  ```shell
  pytest
  ```
* Build documentation:
  In `docs/`
  ```shell
  make clean
  make html
  ```
* Upload to [PyPI](https://pypi.org/):
  ```shell
  twine upload dist/*
  ```

## Authors and acknowledgment

* Tom Verhoeff (Eindhoven University of Technology, Netherlands)

## License

[MIT License](LICENSE.txt)

## Project status

* Under development, but already usable
* Documentation:
  - incomplete
  - Sphinx version still has issues
* Test cases: incomplete
* Functionality:
  - functions only print in mixed Math/Python notation
  - level of detail in tracing cannot be selected
  - limited form of laziness
* [Issues](https://gitlab.tue.nl/t-verhoeff-software/fupy/-/issues)
