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

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, TypeAdapter

from boulderopalscaleupsdk.common.dtypes import Duration, DurationNsLike, ISO8601DatetimeUTCLike
from boulderopalscaleupsdk.common.typeclasses import Combine

T = TypeVar("T")
T2 = TypeVar("T2")
CalibrationStatusT = Literal["approximate", "bad", "good", "stale", "unmeasured"]


class ComponentParameter(BaseModel, Generic[T]):
    dtype: Literal["component-parameter"] = "component-parameter"
    value: T
    err_minus: T | None = None
    err_plus: T | None = None
    calibration_status: CalibrationStatusT = "unmeasured"
    updated_at: ISO8601DatetimeUTCLike | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_value(
        cls,
        value: Any,
        target_type: type[float | int | Duration],
    ) -> "ComponentParameter":
        """
        Create a ComponentParameter instance from a value, ensuring it matches the target type.

        Parameters
        ----------
        value : Any
            The input value to validate and convert.
        target_type : type
            The expected type of the value (e.g., float, int, Duration).

        Returns
        -------
        ComponentParameter
            A validated ComponentParameter instance.

        Raises
        ------
        ValueError
            If the value does not match the target type.
        """
        match value:
            case value if isinstance(value, cls):
                if not isinstance(value.value, target_type):
                    raise TypeError("invalid value type")
                return value
            case _ if target_type in [float, int]:
                return cls(**value)
            case _ if target_type is Duration:
                value_copy = value.copy()
                duration_ns = TypeAdapter(DurationNsLike).validate_python(value_copy.pop("value"))
                return cls(value=duration_ns, **value_copy)  # type: ignore[arg-type]
            case _:
                return cls.model_validate(value)

    @staticmethod
    def combine(
        combine_instance: Combine[T],
    ) -> "Combine[ComponentParameter[T]]":
        def _combine(
            first: ComponentParameter[T],
            other: ComponentParameter[Any],
        ) -> ComponentParameter[T]:
            return ComponentParameter(
                value=combine_instance.combine(first.value, other.value),
                err_minus=combine_instance.combine_option(
                    first.err_minus,
                    other.err_minus,
                ),
                err_plus=combine_instance.combine_option(
                    first.err_plus,
                    other.err_plus,
                ),
                calibration_status=other.calibration_status,
                updated_at=datetime.now(tz=timezone.utc),
            )

        return Combine[ComponentParameter[T]].create(_combine)

    def map(self, fn: Callable[[T], T2]) -> "ComponentParameter[T2]":
        return ComponentParameter(
            value=fn(self.value),
            err_minus=fn(self.err_minus) if self.err_minus is not None else None,
            err_plus=fn(self.err_plus) if self.err_plus is not None else None,
            calibration_status=self.calibration_status,
            updated_at=self.updated_at,
        )

    def merge_with(self, other: "ComponentParameter[T]", combine_value: "Combine[T]"):
        combined = ComponentParameter[T].combine(combine_value).combine(self, other)
        self.value = combined.value
        self.err_minus = combined.err_minus
        self.err_plus = combined.err_plus
        self.calibration_status = combined.calibration_status
        self.updated_at = combined.updated_at


def get_calibration_status_from_thresholds(
    value: float,
    confidence_interval: float,
    good_threshold: float,
    approximate_threshold: float,
) -> CalibrationStatusT:
    if good_threshold <= 0 or approximate_threshold <= 0 or good_threshold >= approximate_threshold:
        raise ValueError(
            f"Invalid thresholds: good: {good_threshold}, approximate: {approximate_threshold}",
        )

    relative_uncertainty = abs(confidence_interval / value)

    if relative_uncertainty < good_threshold:
        return "good"
    if relative_uncertainty < approximate_threshold:
        return "approximate"
    return "bad"


FloatComponentParameter = Annotated[
    ComponentParameter[float],
    BeforeValidator(lambda value: ComponentParameter.from_value(value, float)),
]

DurationComponentParameter = Annotated[
    ComponentParameter[Duration],
    BeforeValidator(lambda value: ComponentParameter.from_value(value, Duration)),
]
