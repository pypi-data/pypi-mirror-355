# Pydantic Types

[![Test](https://github.com/yukihiko-shinoda/pydantic-types/workflows/Test/badge.svg)](https://github.com/yukihiko-shinoda/pydantic-types/actions?query=workflow%3ATest)
[![CodeQL](https://github.com/yukihiko-shinoda/pydantic-types/workflows/CodeQL/badge.svg)](https://github.com/yukihiko-shinoda/pydantic-types/actions?query=workflow%3ACodeQL)
[![Maintainability](https://qlty.sh/badges/11a7c146-f6ee-4d74-8b63-2d2e963ef988/maintainability.svg)](https://qlty.sh/gh/yukihiko-shinoda/projects/pydantic-types)
[![Dependabot](https://flat.badgen.net/github/dependabot/yukihiko-shinoda/pydantic-types?icon=dependabot)](https://github.com/yukihiko-shinoda/pydantic-types/security/dependabot)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydantictypes)](https://pypi.org/project/pydantictypes)
[![Twitter URL](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Fyukihiko-shinoda%2Fpydantic-types)](http://twitter.com/share?text=Pydantic%20Types&url=https://pypi.org/project/pydantictypes/&hashtags=python)

Common used type definitions with Pydantic.

## Advantage

- Out of the box

### Out of the box

You don't need to define customized types for common use cases. This package provides a set of commonly used types that can be directly imported and used in your Pydantic models.

## Quickstart

```bash
pip install pydantictypes
```

## API

### StrictKanjiYenStringToInt

```python
from pydantictypes import StrictKanjiYenStringToInt
class MyModel(BaseModel):
    price: StrictKanjiYenStringToInt
```
This type converts a string representing a price in Japanese yen, written in kanji, to an integer. It raises a `ValueError` if the input is not a valid kanji yen string.

### StringSlashMonthDayOnlyToDatetime

```python
from pydantictypes import StringSlashMonthDayOnlyToDatetime
class MyModel(BaseModel):
    date: StringSlashMonthDayOnlyToDatetime
```
This type converts a string in the format "MM/DD" to a `datetime` object, assuming the current year. It raises a `ValueError` if the input is not in the correct format.

### StringSlashToDateTime

```python
from pydantictypes import StringSlashToDateTime
class MyModel(BaseModel):
    date: StringSlashToDateTime
```
This type converts a string in the format "YYYY/MM/DD" to a `datetime` object. It raises a `ValueError` if the input is not in the correct format.

### ConstrainedStringToOptionalInt

```python
from pydantictypes import ConstrainedStringToOptionalInt
class MyModel(BaseModel):
    optional_int: ConstrainedStringToOptionalInt
```
This type converts a string to an optional integer. If the string is empty, it returns `None`. If the string is not a valid integer, it raises a `ValueError`.

### StrictStringWithCommaToInt

```python
from pydantictypes import StrictStringWithCommaToInt
class MyModel(BaseModel):
    number: StrictStringWithCommaToInt
```
This type converts a string with commas (e.g., "1,000") to an integer. It raises a `ValueError` if the input is not a valid string with commas.

### StrictStringWithCommaToOptionalInt

```python
from pydantictypes import StrictStringWithCommaToOptionalInt
class MyModel(BaseModel):
    optional_number: StrictStringWithCommaToOptionalInt
```
This type converts a string with commas to an optional integer. If the string is empty, it returns `None`. If the string is not a valid string with commas, it raises a `ValueError`.

### StrictSymbolYenStringToInt

```python
from pydantictypes import StrictSymbolYenStringToInt
class MyModel(BaseModel):
    price: StrictSymbolYenStringToInt
```
This type converts a string representing a price in Japanese yen, written with the yen symbol (¥), to an integer. It raises a `ValueError` if the input is not a valid symbol yen string.

## Credits

This package was created with [Cookiecutter] and the [yukihiko-shinoda/cookiecutter-pypackage] project template.

[Cookiecutter]: https://github.com/audreyr/cookiecutter
[yukihiko-shinoda/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
