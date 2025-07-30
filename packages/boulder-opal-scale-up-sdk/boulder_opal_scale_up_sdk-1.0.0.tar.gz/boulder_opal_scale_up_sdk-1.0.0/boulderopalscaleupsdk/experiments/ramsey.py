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

from pydantic import PrivateAttr

from .common import Experiment

DEFAULT_RECYCLE_DELAY_NS = 10_000
DEFAULT_SHOT_COUNT = 400


class Ramsey(Experiment):
    """
    Parameters for running a Ramsey experiment.

    Parameters
    ----------
    qubit : int
        The qubit whose resonator to target in the experiment.
    max_delay_ns : int
        The maximum delay time, in nanoseconds.
    min_delay_ns : int
        The minimum delay time, in nanoseconds.
    delay_step_ns : int
        The step for generating the list of delays, in nanoseconds.
    detuning : float
        The difference between the drive signal frequency and the qubit frequency,
        in Hz.
    recycle_delay_ns : float, optional
        The delay time between consecutive shots of the experiment, in nanoseconds.
        Defaults to 10000 ns.
    shot_count : int, optional
        The number of shots to be taken in the experiment.
        Defaults to 400.
    """

    _experiment_name: str = PrivateAttr("ramsey")

    qubit: int
    max_delay_ns: int
    min_delay_ns: int
    delay_step_ns: int
    detuning: float
    recycle_delay_ns: int = DEFAULT_RECYCLE_DELAY_NS
    shot_count: int = DEFAULT_SHOT_COUNT
