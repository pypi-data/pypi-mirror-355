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

import logging
import os
from typing import Literal
from unittest.mock import patch

from pydantic import BaseModel, Field, model_validator

from boulderopalscaleupsdk.common.dtypes import Duration, DurationNsLike, Self, TimeUnit
from boulderopalscaleupsdk.third_party.quantum_machines.config import (
    ControllerConfigType,
    OctaveConfig121,
    OPX1000ControllerConfigType,
)
from boulderopalscaleupsdk.third_party.quantum_machines.constants import (
    MIN_TIME_OF_FLIGHT,
    QUA_CLOCK_CYCLE,
)

from .base import BaseControllerInfo

# Disable QM logging and telemetry
os.environ["QM_DISABLE_STREAMOUTPUT"] = "True"  # Used in 1.1.0
_qm_logger = logging.getLogger("qm")
_qm_logger.disabled = True

# Disable unwanted telemetry/logging modules in QM
_qm_patch_targets = [
    "qm._loc._get_loc",
    "qm.program.expressions._get_loc",
    "qm.program.StatementsCollection._get_loc",
    "qm.qua._get_loc",
    "qm.qua._dsl._get_loc",
    "qm.qua._expressions._get_loc",
    "qm.qua.AnalogMeasureProcess._get_loc",
    "qm.qua.DigitalMeasureProcess._get_loc",
    "qm.datadog_api.DatadogHandler",
]
for target in _qm_patch_targets:
    try:
        _m = patch(target).__enter__()
        _m.return_value = ""
    except (AttributeError, ModuleNotFoundError):  # noqa: PERF203
        pass

PortRef = str
OctaveRef = str
ControllerRef = str
PortNum = int
PortMapping = tuple[OctaveRef, PortNum]


class OctaveConfig(OctaveConfig121):
    host: str | None = Field(default=None)
    port: int | None = Field(default=None)

    def to_qm_octave_config_121(self) -> OctaveConfig121:
        return OctaveConfig121.model_validate(self.model_dump())


class DrivePortConfig(BaseModel):
    port_type: Literal["drive"] = "drive"
    port_mapping: PortMapping


class FluxPortConfig(BaseModel):
    port_type: Literal["flux"] = "flux"
    port_mapping: PortMapping


class ReadoutPortConfig(BaseModel):
    port_type: Literal["readout"] = "readout"
    port_mapping: PortMapping
    time_of_flight: DurationNsLike
    smearing: DurationNsLike = Field(default=Duration(0, TimeUnit.NS))

    @model_validator(mode="after")
    def _validate_readout_port_config(self) -> Self:
        min_time_of_flight_ns = MIN_TIME_OF_FLIGHT.convert(TimeUnit.NS).value
        time_of_flight_ns = self.time_of_flight.convert(TimeUnit.NS).value
        smearing_ns = self.smearing.convert(TimeUnit.NS).value
        qua_clock_cycle_ns = QUA_CLOCK_CYCLE.convert(TimeUnit.NS).value

        if time_of_flight_ns < min_time_of_flight_ns:
            raise ValueError(f"time_of_flight must be >= {MIN_TIME_OF_FLIGHT}")

        if time_of_flight_ns % qua_clock_cycle_ns != 0:
            raise ValueError(f"time_of_flight must be a multiple of {QUA_CLOCK_CYCLE}")

        if smearing_ns > time_of_flight_ns - 8:
            raise ValueError(f"smearing must be at most {time_of_flight_ns - 8} ns")

        return self


OPXControllerConfig = ControllerConfigType
OPX1000ControllerConfig = OPX1000ControllerConfigType


class QuantumMachinesControllerInfo(BaseControllerInfo):
    """
    QuantumMachinesControllerInfo is a data model that represents the configuration
    and port settings for quantum machine controllers.

    NOTE: Interface must match OPX Config for first set of parameters, remainder are ours
        https://docs.quantum-machines.co/1.2.1/assets/qua_config.html#/paths/~1/get

    Attributes
    ----------
    controllers : dict[ControllerRef, OPXControllerConfig | OPX1000ControllerConfig]
        A dictionary mapping controller references to their respective configurations.
        The configurations can be either OPXControllerConfig or OPX1000ControllerConfig.
        Derived from OPX Config.
    octaves : dict[OctaveRef, OctaveConfig]
        A dictionary mapping octave references to their respective configurations.
        Derived from OPX Config.
    port_config : dict[PortRef, DrivePortConfig | FluxPortConfig | ReadoutPortConfig]
        A dictionary mapping port references to their respective port configurations.
        The configurations can be DrivePortConfig, FluxPortConfig, or ReadoutPortConfig.
        Not derived from OPX Config, this is our custom config.
    """

    controllers: dict[ControllerRef, OPXControllerConfig | OPX1000ControllerConfig] = Field(
        default={},
    )
    octaves: dict[OctaveRef, OctaveConfig] = Field(default={})
    port_config: dict[PortRef, DrivePortConfig | FluxPortConfig | ReadoutPortConfig]
