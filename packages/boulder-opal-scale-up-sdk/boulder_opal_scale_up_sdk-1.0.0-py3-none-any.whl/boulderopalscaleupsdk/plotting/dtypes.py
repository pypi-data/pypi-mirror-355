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

import base64
from typing import Annotated, Any, Literal

import numpy as np
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    PlainSerializer,
    ValidationError,
    model_validator,
)
from pydantic.dataclasses import dataclass


def _array_validator(value: Any) -> np.ndarray:
    if isinstance(value, dict):
        array = np.frombuffer(base64.b64decode(value["data"]), dtype=value["dtype"]).reshape(
            value["shape"],
        )
    else:
        array = np.asarray(value, order="C")

    if array.dtype == np.dtypes.ObjectDType:
        raise ValidationError("Invalid array.")

    return array


def _array_serializer(array: np.ndarray) -> dict[str, Any]:
    return {
        "data": base64.b64encode(array),
        "dtype": str(array.dtype),
        "shape": array.shape,
    }


_SerializableArray = Annotated[
    np.ndarray,
    BeforeValidator(_array_validator),
    PlainSerializer(_array_serializer),
]


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class PlotData1D:
    """
    A class to represent 1D plot data with optional error bars.

    Attributes
    ----------
    x : np.ndarray
        The x-coordinates of the data points.
    y : np.ndarray
        The y-coordinates of the data points.
    x_error : np.ndarray or None, optional
        The errors in the x-coordinates. Defaults to None.
    y_error : np.ndarray or None, optional
        The errors in the y-coordinates. Defaults to None.
    label : str or None, optional
        The label for the data to display in the legend. Defaults to None.
    """

    x: _SerializableArray
    y: _SerializableArray
    x_error: _SerializableArray | None = None
    y_error: _SerializableArray | None = None
    label: str | None = None

    def __post_init__(self):
        if self.x.ndim != 1:
            raise ValueError("x must be 1D.")
        if self.y.ndim != 1:
            raise ValueError("y must be 1D.")
        if len(self.x) != len(self.y):
            raise ValueError("The length of x and y must match.")

        if self.x_error is not None and self.x_error.shape != self.x.shape:
            raise ValueError("The shapes of x and x_error must match.")
        if self.y_error is not None and self.y_error.shape != self.y.shape:
            raise ValueError("The shapes of y and y_error must match.")


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class PlotData2D:
    """
    A class to represent 2D plot data.

    Attributes
    ----------
    x : np.ndarray
        The x-coordinates of the data points.
    y : np.ndarray
        The y-coordinates of the data points.
    z : np.ndarray
        The z-values corresponding to each (x, y) pair.
    label : str or None, optional
        The label for the data to display in the legend. Defaults to None.
    """

    x: _SerializableArray
    y: _SerializableArray
    z: _SerializableArray
    label: str | None = None

    def __post_init__(self):
        if self.x.ndim != 1:
            raise ValueError("x must be 1D.")
        if self.y.ndim != 1:
            raise ValueError("y must be 1D.")
        if self.z.ndim != 2:
            raise ValueError("z must be 2D.")
        if self.z.shape != (len(self.x), len(self.y)):
            raise ValueError("The shape of z must be (len(x), len(y)).")


@dataclass
class Marker:
    x: float
    y: float
    label: str
    color: str
    symbol: Literal["star"]


@dataclass
class VLine:
    value: float
    line_dash: Literal["dash"]
    color: str | None = None


class Plot(BaseModel):
    """
    Data to plot the results of an experiment.

    Parameters
    ----------
    heatmap : PlotData2D or None, optional
        The 2D experimental data.
        If provided, it's plotted as a heatmap.
    heatmap_text : bool, optional
        If True, the heatmap displays the values as text.
        Defaults to False.
    points : PlotData1D or None, optional
        The 1D experimental data.
        If provided, it's plotted as a scatter plot.
    best_fit : PlotData1D or None, optional
        The best fit on the experimental data.
        If provided, it's plotted as a line plot.
    reference_fit : PlotData1D or None, optional
        A reference fit on the experimental data.
        If provided, it's plotted as a line plot.
    markers : list[Markers] or None, optional
        Markers to add to the plot.
    vlines : list[VLine] or None, optional
        Vertical lines to add to the plot.
    title : str or None, optional
        The title of the plot.
    xticks : list[float] or None, optional
        The values at which x-ticks are placed.
        Must be specified alongside xticklabels. Defaults to None.
    xticklabels : list[str] or None, optional
        The labels for the x-ticks.
        Must be specified alongside xticks. Defaults to None.
    yticks : list[float] or None, optional
        The values at which y-ticks are placed.
        Must be specified alongside yticklabels. Defaults to None.
    yticklabels : list[str] or None, optional
        The labels for the y-ticks.
        Must be specified alongside xticks. Defaults to None.
    x_label : str, optional
        The label for the x-axis. Defaults to "X-axis".
    y_label : str, optional
        The label for the y-axis. Defaults to "Y-axis".
    reverse_yaxis : bool, optional
        If True, the y-axis is reversed. Defaults to False.
    fit_report : str or None, optional
        An optional report for the fit.
    """

    heatmap: PlotData2D | None = None
    heatmap_text: bool = False
    points: PlotData1D | None = None
    best_fit: PlotData1D | None = None
    reference_fit: PlotData1D | None = None
    markers: list[Marker] | None = None
    vlines: list[VLine] | None = None
    title: str | None = None
    xticks: list[float] | None = None
    xticklabels: list[str] | None = None
    yticks: list[float] | None = None
    yticklabels: list[str] | None = None
    x_label: str = "X-axis"
    y_label: str = "Y-axis"
    reverse_yaxis: bool | None = False
    fit_report: str | None = None

    @model_validator(mode="after")
    def validate_ticks(self) -> "Plot":
        # Check ticks and ticklabels consistency.
        if not ((self.xticks is not None) ^ (self.xticklabels is None)):
            raise ValueError("Both xticks and xticklabels must be provided together.")

        if not ((self.yticks is not None) ^ (self.yticklabels is None)):
            raise ValueError("Both yticks and yticklabels must be provided together.")

        return self
