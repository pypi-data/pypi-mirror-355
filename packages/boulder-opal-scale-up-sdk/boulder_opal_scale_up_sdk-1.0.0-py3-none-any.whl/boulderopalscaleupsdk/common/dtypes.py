# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.

from __future__ import annotations

from typing import overload

__all__ = [
    "Duration",
    "Self",
    "TimeUnit",
]

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal

import numpy as np
from dateutil.parser import isoparse
from pydantic import BeforeValidator, PlainSerializer, TypeAdapter
from pydantic.dataclasses import dataclass as pydantic_dataclass

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class BaseType: ...


class FrequencyUnit(str, Enum):
    Hz = "Hz"


@pydantic_dataclass
class Frequency:
    value: float
    unit: FrequencyUnit  # No default to guarantee clarity of units

    @classmethod
    def from_float_hz(cls, value: float) -> Frequency:
        return cls(value, FrequencyUnit.Hz)

    def to_int_hz(self) -> int:
        return int(self.to_float_hz())

    def to_float_hz(self) -> float:
        match self.unit:
            case FrequencyUnit.Hz:
                return self.value

    def __gt__(self, other: Frequency) -> bool:
        return self.to_float_hz() > other.to_float_hz()

    def __ge__(self, other: Frequency) -> bool:
        return self.to_float_hz() >= other.to_float_hz()

    def __lt__(self, other: Frequency) -> bool:
        return self.to_float_hz() < other.to_float_hz()

    def __le__(self, other: Frequency) -> bool:
        return self.to_float_hz() <= other.to_float_hz()

    def __sub__(self, rhs: Frequency) -> Frequency:
        if self.unit == rhs.unit:
            return Frequency(self.value - rhs.value, self.unit)
        raise NotImplementedError

    def __add__(self, rhs: Frequency) -> Frequency:
        if self.unit == rhs.unit:
            return Frequency(self.value + rhs.value, self.unit)
        raise NotImplementedError

    def __abs__(self) -> Frequency:
        return Frequency(abs(self.value), self.unit)

    def __str__(self):
        return f"{self.value} {self.unit.value}"

    @overload  # Division by a scalar: e.g. 4.4 Hz // 2.0 = 2.2 Hz
    def __truediv__(self, rhs: float) -> Frequency: ...

    @overload
    def __truediv__(self, rhs: Frequency) -> float: ...

    def __truediv__(self, rhs: float | Frequency) -> Frequency | float:
        if isinstance(rhs, Frequency):
            return self.to_float_hz() / rhs.to_float_hz()
        return Frequency(self.value / rhs, self.unit)

    @overload  # Floor division by a scalar: e.g. 2.2 Hz // 2.0 = 1 Hz
    def __floordiv__(self, rhs: float) -> Frequency: ...

    @overload
    def __floordiv__(self, rhs: Frequency) -> float: ...

    def __floordiv__(self, rhs: float | Frequency) -> Frequency | float:
        if isinstance(rhs, Frequency):
            return self.to_float_hz() // rhs.to_float_hz()
        return Frequency(self.value // rhs, self.unit)

    def __mul__(self, rhs: float) -> Frequency:
        return Frequency(self.value * rhs, self.unit)

    def __rmul__(self, lhs: float) -> Frequency:
        return self.__mul__(lhs)


class TimeUnit(str, Enum):
    S = "s"
    MS = "ms"
    US = "us"
    NS = "ns"
    DT = "dt"


_SI_TIME = Literal[TimeUnit.S, TimeUnit.MS, TimeUnit.US, TimeUnit.NS]


@pydantic_dataclass(order=True)
class Duration(BaseType):
    """
    A wrapper of _SiDuration and _DtDuration to manage the conversion.
    """

    value: int = field(compare=False)
    unit: TimeUnit = field(compare=False)
    dtype: Literal["duration"] = "duration"
    _value: _SiDuration | _DtDuration = field(init=False, repr=False)

    def __post_init__(self):
        self._value = (
            _DtDuration(self.value)
            if self.unit == TimeUnit.DT
            else _SiDuration(self.value, self.unit)
        )

    def is_si(self) -> bool:
        return self.unit != TimeUnit.DT

    @staticmethod
    def from_si(d: Duration, name: str) -> Duration:
        if d.unit == TimeUnit.DT:
            raise TypeError(f"{name} must use SI time unit.")
        return d

    @staticmethod
    def from_intlike(val: float, unit: TimeUnit) -> Duration:
        if not np.double(val).is_integer():
            raise ValueError("fail to create a Duration object. value must be an integer.")
        return Duration(int(val), unit)

    def convert(self, target: Duration | _SI_TIME) -> Duration:
        """
        In particular, we only allow the following conversions:

        # ((1000, "ms"), "s") -> (1, "s")
        (_SiDuration, _SI_TIME) -> _SiDuration

        # ((4, "ns"), (2, "ns")) -> (2, "dt")
        (_SiDuration, _SiDuration) -> _DtDuration

        # ((2, "dt"), (2, "ns")) -> (4, "ns")
        (_DtDuration, _SiDuration) _> _SiDuration
        """
        match self._value, getattr(target, "_value", target):
            case _SiDuration(
                _,
                _,
            ), TimeUnit.S | TimeUnit.MS | TimeUnit.US | TimeUnit.NS:
                converted = self._value.convert_to_si(target)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
            case _SiDuration(_, _), _SiDuration(_, _):
                converted = self._value.convert_to_dt(target)  # type: ignore[arg-type, assignment] # pyright: ignore[reportArgumentType]
            case _DtDuration(_, _), _SiDuration(_, _):
                converted = self._value.convert(target)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
            case _:
                raise TypeError(f"cant't convert type {self.unit} to {target}")
        return Duration(converted.value, converted.unit)


@dataclass(order=True)
class _DtDuration(BaseType):
    value: int
    unit: Literal[TimeUnit.DT] = TimeUnit.DT

    def convert(self, target: _SiDuration) -> _SiDuration:
        return _SiDuration(self.value * target.value, target.unit)


@dataclass(order=True)
class _SiDuration(BaseType):
    value: int = field(compare=False)
    unit: _SI_TIME = field(compare=False)
    _np_rep: np.timedelta64 = field(init=False, repr=False)

    def __post_init__(self):
        err = TypeError(
            f"value must be an integer, got {self.value}{self.unit}. Choose a different unit to "
            "scale it.",
        )
        dec = Decimal(self.value)
        exponent = dec.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < 0:  # pragma: no cover
            raise err

        self.value = int(self.value)
        try:
            self._np_rep = np.timedelta64(self.value, self.unit)
        except ValueError as e:
            raise err from e

    def convert_to_dt(self, clock: _SiDuration) -> _DtDuration:
        try:
            converted_si = self.convert_to_si(clock.unit)
        except TypeError as e:
            raise TypeError(
                "fail to convert to dt type. Consider rescaling the clock time.",
            ) from e
        val = np.double(converted_si.value / clock.value)
        # N.B, this might be too strict. Some rounding might be necessary.
        if not val.is_integer():
            raise TypeError(
                "fail to convert to dt type. Consider rescaling the clock time.",
            )
        return _DtDuration(int(val))

    def convert_to_si(self, unit: _SI_TIME) -> _SiDuration:
        if self._np_rep is None:
            raise TypeError("`convert` only support SI time unit.")
        val: np.float64 = self._np_rep / np.timedelta64(1, unit)
        if not val.is_integer():
            raise TypeError(
                f"fail to convert to {unit} with {self.value}{self.unit}.",
            )
        return _SiDuration(int(val), unit)

    def to_seconds(self) -> float:
        return float(self._np_rep / np.timedelta64(1, "s"))


def ensure_frequency_hz(value: Any) -> Any:
    match value:
        case Frequency():
            return value
        case float() | int():
            return Frequency(value, FrequencyUnit.Hz)
        case dict():
            return TypeAdapter(Frequency).validate_python(value)
        case _:
            raise ValueError("Frequency needs to be numeric.")


FrequencyHzLike = Annotated[
    Frequency,
    BeforeValidator(ensure_frequency_hz),
    PlainSerializer(lambda x: x.to_float_hz(), return_type=float),
]


def ensure_duration_ns(value: Any) -> Any:
    match value:
        case Duration():
            return value.convert(TimeUnit.NS)
        case float() | int():
            return Duration.from_intlike(value, TimeUnit.NS)
        case dict():
            return TypeAdapter(Duration).validate_python(value)
        case _:
            raise ValueError("Duration needs to be numeric")


DurationNsLike = Annotated[Duration, BeforeValidator(ensure_duration_ns)]


@pydantic_dataclass
class ISO8601Datetime:
    value: datetime

    def __post_init__(self):
        self.value = _validate_iso_datetime(self.value)

    def __str__(self):
        return _serialize_datetime(self.value)

    def strftime(self, fmt: str) -> str:
        """
        Format the datetime value using the given format string.

        Parameters
        ----------
        fmt : str
            The format string to use for formatting.

        Returns
        -------
        str
            The formatted datetime string.
        """
        return self.value.strftime(fmt)


def _validate_iso_datetime(value: Any) -> datetime:
    def _raise_invalid_timezone_error():
        raise ValueError("Datetime must be in UTC timezone.")

    if isinstance(value, ISO8601Datetime):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) != timedelta(0):
            _raise_invalid_timezone_error()
        else:
            return value
    if isinstance(value, str):
        try:
            parsed_datetime = isoparse(value)
            if parsed_datetime.tzinfo is None or parsed_datetime.tzinfo.utcoffset(
                parsed_datetime,
            ) != timedelta(0):
                _raise_invalid_timezone_error()
            else:
                return parsed_datetime
        except Exception as e:
            raise ValueError("Invalid ISO8601 datetime string.") from e
    raise ValueError(
        "Value must be a datetime object, an ISO8601Datetime instance, or a valid ISO8601 string.",
    )


def _serialize_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) != timedelta(0):
        raise ValueError("Datetime must be in UTC timezone.")
    return value.isoformat()


ISO8601DatetimeUTCLike = Annotated[
    datetime,
    BeforeValidator(_validate_iso_datetime),
    PlainSerializer(_serialize_datetime),
]
