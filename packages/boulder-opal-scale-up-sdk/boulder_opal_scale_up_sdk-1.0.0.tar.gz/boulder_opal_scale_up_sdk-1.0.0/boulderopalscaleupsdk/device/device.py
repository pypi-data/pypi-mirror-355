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

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from boulderopalscaleupsdk.device.controller.quantum_machines import QuantumMachinesControllerInfo
from boulderopalscaleupsdk.device.processor import SuperconductingProcessor


class Device(BaseModel):
    """Device specification."""

    processor: SuperconductingProcessor  # | OtherProcessorTypes
    controller_info: QuantumMachinesControllerInfo  # | OtherControllerInfoTypes


@dataclass
class InvalidDevice:
    message: str


@dataclass
class InvalidDeviceComponent:
    message: str
