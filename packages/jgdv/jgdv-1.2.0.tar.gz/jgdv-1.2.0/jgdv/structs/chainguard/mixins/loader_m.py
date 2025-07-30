#!/usr/bin/env python3
"""

"""

# Imports:
##-- builtin imports
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
import tomllib
from uuid import UUID, uuid1

# ##-- end stdlib imports

##-- end builtin imports

# ##-- 1st party imports
from .._interface import TomlTypes

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard, TypeVar
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type T = TypeVar('T')

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class TomlLoader_m:
    """ Mixin for loading toml files """

    @classmethod
    def read(cls:T, text:str) -> T:
        logging.debug("Reading ChainGuard for text")
        try:
            return cls(tomllib.loads(text))
        except Exception as err:
            raise IOError("ChainGuard Failed to Load: ", text, err.args) from err

    @classmethod
    def from_dict(cls, data:dict[str, TomlTypes]) -> Self:
        logging.debug("Making ChainGuard from dict")
        try:
            return cls(data)
        except Exception as err:
            raise IOError("ChainGuard Failed to Load: ", data, err.args) from err

    @classmethod
    def load(cls, *paths:str|pl.Path) -> Self:
        logging.debug("Creating ChainGuard for %s", paths)
        texts = []
        for path in paths:
            texts.append(pl.Path(path).read_text())
        else:
            try:
                return cls(tomllib.loads("\n".join(texts)))
            except tomllib.TOMLDecodeError as err:
                raise IOError("Failed to Load Toml", *err.args, paths) from err

    @classmethod
    def load_dir(cls, dirp:str|pl.Path) -> Self:
        logging.debug("Creating ChainGuard for directory: %s", str(dirp))
        try:
            texts = []
            for path in pl.Path(dirp).glob("*.toml"):
                texts.append(path.read_text())

            return cls(tomllib.loads("\n".join(texts)))
        except Exception as err:
            raise IOError("ChainGuard Failed to load Directory: ", dirp, err.args) from err
