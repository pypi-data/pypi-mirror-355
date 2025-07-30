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

from copy import deepcopy
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel, Field

from boulderopalscaleupsdk.common.dtypes import (
    Duration,
    TimeUnit,
)
from boulderopalscaleupsdk.device.common import (
    Component,
    ComponentRef,
    Processor,
)
from boulderopalscaleupsdk.device.processor import (
    ComponentParameter,
    DurationComponentParameter,
    FloatComponentParameter,
)


# Retrieval data models
class Transmon(Component[Literal["tunable"]]):
    dtype: Literal["transmon"] = "transmon"
    traits: list[Literal["tunable"]] = Field(default=["tunable"])

    freq_01: FloatComponentParameter | None = Field(
        default=None,
        json_schema_extra={"display": {"label": "freq_01", "unit": "MHz", "scale": 1e-6}},
    )
    anharm: FloatComponentParameter | None = Field(
        default=None,
        json_schema_extra={"display": {"label": "anharm", "unit": "MHz", "scale": 1e-6}},
    )
    t1: DurationComponentParameter = Field(
        default=ComponentParameter(value=Duration(0, TimeUnit.NS)),
        json_schema_extra={"display": {"label": "t1", "unit": "µs", "scale": 1e6}},
    )
    t2: DurationComponentParameter = Field(
        default=ComponentParameter(value=Duration(0, TimeUnit.NS)),
        json_schema_extra={"display": {"label": "t2", "unit": "µs", "scale": 1e6}},
    )
    t2_echo: DurationComponentParameter = Field(
        default=ComponentParameter(value=Duration(0, TimeUnit.NS)),
        json_schema_extra={"display": {"label": "t2_echo", "unit": "µs", "scale": 1e6}},
    )
    x_vp: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "x_vp", "unit": "V", "scale": 1}},
    )
    sx_vp: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "sx_vp", "unit": "V", "scale": 1}},
    )

    # Tunable transmon parameters.
    dc_bias: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "dc_bias", "unit": "V", "scale": 1}},
    )
    fmax_bias: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "fmax_bias", "unit": "V", "scale": 1}},
    )
    bias_period: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "bias_period", "unit": "V", "scale": 1}},
    )


class Resonator(Component[Literal["dispersive"]]):
    dtype: Literal["resonator"] = "resonator"
    traits: list[Literal["dispersive"]] = Field(default=["dispersive"])

    frequency_high: FloatComponentParameter | None = Field(
        default=None,
        json_schema_extra={"display": {"label": "frequency_high", "unit": "MHz", "scale": 1e-6}},
    )
    frequency_low: FloatComponentParameter | None = Field(
        default=None,
        json_schema_extra={"display": {"label": "frequency_low", "unit": "MHz", "scale": 1e-6}},
    )
    kappa_low: FloatComponentParameter | None = Field(
        default=None,
        json_schema_extra={"display": {"label": "kappa_low", "unit": "MHz", "scale": 1e-6}},
    )
    kappa_high: FloatComponentParameter | None = Field(
        default=None,
        json_schema_extra={"display": {"label": "kappa_high", "unit": "MHz", "scale": 1e-6}},
    )
    vp_low: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "vp_low", "unit": "V", "scale": 1}},
    )
    vp_high: FloatComponentParameter = Field(
        default=ComponentParameter(value=0.0),
        json_schema_extra={"display": {"label": "vp_high", "unit": "V", "scale": 1}},
    )


class Port(Component[Literal["drive", "readout", "flux"]]):
    dtype: Literal["port"] = "port"
    traits: list[Literal["flux", "drive", "readout"]] = Field(
        default=["drive", "readout", "flux"],
    )


class Filter(Component[Literal["filter"]]):
    dtype: Literal["filter"] = "filter"
    traits: list = Field(default=[])


class Feedline(Component[Literal["feedline"]]):
    dtype: Literal["feedline"] = "feedline"
    traits: list = Field(default=[])


SuperconductingComponentType = Transmon | Resonator | Port | Feedline | Filter


class Edge(BaseModel):
    dtype: Literal["capacitive-coupling", "inductive-coupling"]
    u: str
    v: str


class TemplateParam(BaseModel):
    template: str
    vars: dict[int, list[str]]


class ProcessorTemplate(BaseModel):
    elements: dict[str, Transmon | Resonator | Port | Feedline | Filter]
    edges: list[Edge]


class SuperconductingProcessorTemplate(BaseModel):
    build: list[TemplateParam]
    templates: dict[str, ProcessorTemplate]
    device_parameters: dict[str, Transmon | Resonator | Port | Feedline | Filter] = Field(
        default={},
    )


class SuperconductingProcessor(Processor):
    nodes: dict[ComponentRef, SuperconductingComponentType]
    edges: list[Edge]

    @staticmethod
    def from_template(template: SuperconductingProcessorTemplate) -> "SuperconductingProcessor":
        _qpu = SuperconductingProcessor(nodes={}, edges=[])
        for build in template.build:
            qpu_template = template.templates[build.template]
            for idx, subs in build.vars.items():
                for sub in subs:
                    for k, template_params in qpu_template.elements.items():
                        ref = k.replace(f"${idx}", sub)
                        params = template.device_parameters.get(ref)
                        p = deepcopy(params or template_params)
                        p.traits = template_params.traits  # type: ignore[reportAttributeAccessIssue]
                        p = _coerce_component_params(p)
                        _qpu.nodes[ref] = p

                    for edge in qpu_template.edges:
                        _qpu.edges.append(
                            Edge(
                                u=edge.u.replace(f"${idx}", sub),
                                v=edge.v.replace(f"${idx}", sub),
                                dtype=edge.dtype,
                            ),
                        )
        return _qpu

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SuperconductingProcessor":
        """
        Deserializes a SuperconductingProcessor instance from a dictionary.
        """
        return SuperconductingProcessor.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the SuperconductingProcessor instance into a dictionary.
        """
        return self.model_dump()

    def update_component(self, component_id: str, **params: Any) -> None:
        """
        Update the parameters of a specific component.

        Parameters
        ----------
        component_id : str
            The ID of the component to update.
        **params : Any
            The parameters to update, provided as keyword arguments.

        Raises
        ------
        KeyError
            If the component with the given ID does not exist.
        ValueError
            If the component does not support the provided parameters.
        ValidationError
            If the updated parameters do not conform to the expected schema.
        """
        if component_id not in self.nodes:
            raise KeyError(f"Component with ID '{component_id}' does not exist.")

        component = self.nodes[component_id]
        replacement_component = {
            k: ComponentParameter(value=v).model_dump()
            if k not in ["dtype", "traits"] and v is not None
            else v
            for k, v in params.items()
        }
        self.nodes[component_id] = type(component).model_validate(replacement_component)

    def get_component(self, component_id: str) -> SuperconductingComponentType:
        """
        Retrieve the parameters of a specific component.

        Parameters
        ----------
        component_id : str
            The ID of the component.

        Returns
        -------
        dict
            A dictionary of the component's parameters.
        """
        return self.nodes[component_id]


def _coerce_component_params(
    component: SuperconductingComponentType,
) -> SuperconductingComponentType:
    annotations = component.__annotations__

    for field_name in component.model_fields:
        expected_type = annotations.get(field_name)
        value = getattr(component, field_name)

        if not isinstance(value, ComponentParameter):
            continue

        def _unwrap_annotated(tp):
            """Unwrap Annotated[...] -> original type."""
            if get_origin(tp) is Annotated:
                return get_args(tp)[0]
            return tp

        def _unwrap_optional(tp):
            """Unwrap Optional[T] -> T."""
            if get_origin(tp) is Union:
                args = [t for t in get_args(tp) if t is not type(None)]
                if len(args) == 1:
                    return args[0]
            return tp

        expected_type = _unwrap_optional(expected_type)
        expected_type = _unwrap_annotated(expected_type)

        if not isinstance(expected_type, type) or not issubclass(expected_type, ComponentParameter):
            continue

        try:
            dumped = value.model_dump()
            coerced = expected_type(**dumped)
            setattr(component, field_name, coerced)
        except Exception as e:
            raise ValueError(
                f"Failed to coerce field '{field_name}' of type "
                "'{expected_type}' with value '{value}': {e}",
            ) from e

    return component
