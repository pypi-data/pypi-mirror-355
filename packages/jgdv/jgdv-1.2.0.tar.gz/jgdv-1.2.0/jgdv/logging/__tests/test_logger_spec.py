#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202, B011

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports


##--|
from ..logger_spec import LoggerSpec
##--|

# ##-- types
# isort: off
# General
import abc
import collections.abc
import typing
import types
from typing import cast, assert_type, assert_never
from typing import Generic, NewType, Never
from typing import no_type_check, final, override, overload
# Protocols and Interfaces:
from typing import Protocol, runtime_checkable
# from . import _interface as API # noqa: N812
# Dataclasses:
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError


#
if typing.TYPE_CHECKING:
    from typing import Final, ClassVar, Any, Self
    from typing import Literal, LiteralString
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    from jgdv import Maybe

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:
class TestLoggerSpec:

    ##--|
    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133

    def test_basic(self):
        match LoggerSpec(name="test"):
            case LoggerSpec():
                assert(True)
            case x:
                assert(False), x

    ##--|
    @pytest.mark.skip
    def test_todo(self):
        pass
