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

# pyright: reportPrivateImportUsage=false
"""qm-qua imports.

This module standardizes all the qm-qua imports across the various versions we will
support.
"""

__all__ = [
    "Constants",
    "QuaExpression",
    "QuaProgram",
    "version",
]


import importlib.metadata

from packaging.version import Version

version = Version(importlib.metadata.version("qm-qua"))
if version >= Version("1.2.0"):
    from qm.api.models.capabilities import OPX_FEM_IDX
    from qm.program import Program as QuaProgram
    from qm.qua._expressions import QuaExpression
else:
    from qm.qua import Program as QuaProgram  # type: ignore[attr-defined,no-redef]
    from qm.qua._dsl import (  # type: ignore[attr-defined,no-redef]
        _Expression as QuaExpression,  # pyright: ignore[reportAttributeAccessIssue]
    )

    OPX_FEM_IDX = None  # type: ignore[assignment]


class Constants:
    """QM-Qua constants."""

    opx_fem_idx: int | None = OPX_FEM_IDX
    """The default FEM port for OPX. Only available for >=1.2.0"""
