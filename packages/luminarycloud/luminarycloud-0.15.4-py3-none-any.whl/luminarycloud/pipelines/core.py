# Copyright 2025 Luminary Cloud, Inc. All Rights Reserved.
from abc import ABC, abstractmethod
from dataclasses import is_dataclass, fields
from typing import Type, TypeVar, Generic
import re
import yaml

from .._helpers.warnings import experimental
from ..pipeline_util.yaml import ensure_yamlizable


class PipelineParameter(ABC):
    """
    Base class for all concrete PipelineParameters.
    """

    def __init__(self, name: str):
        self.name = name
        self._validate()

    @property
    def type(self) -> str:
        return self._type()

    @abstractmethod
    def _type(self) -> str:
        pass

    def _validate(self) -> None:
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.name):
            raise ValueError(
                "name must only contain alphanumeric characters, underscores and hyphens"
            )

    def _add_to_params(self, params: dict) -> None:
        if self.name in params and params[self.name]["type"] != self.type:
            raise ValueError(
                f"Parameter name {self.name} used with multiple types: {params[self.name]['type']} != {self.type}"
            )
        params[self.name] = {"type": self.type}

    def _to_pipeline_dict(self) -> tuple[dict, list["PipelineParameter"]]:
        return {"$pipeline_param": self.name}, [self]


class PipelineInput:
    """
    A named input for an Operator instance (i.e. a Task). Explicitly connected to a PipelineOutput.
    """

    def __init__(self, upstream_output: "PipelineOutput", owner: "Operator", name: str):
        self.upstream_output = upstream_output
        self.owner = owner
        self.name = name

    def _to_dict(self, id_for_task: dict) -> dict:
        if self.upstream_output.owner not in id_for_task:
            raise ValueError(
                f"Task {self.owner} depends on a task, {self.upstream_output.owner}, that isn't in the Pipeline. Did you forget to add it?"
            )
        upstream_task_id = id_for_task[self.upstream_output.owner]
        upstream_output_name = self.upstream_output.name
        return {self.name: f"{upstream_task_id}.{upstream_output_name}"}


class PipelineOutput(ABC):
    """
    A named output for an Operator instance (i.e. a Task). Can be used to spawn any number of
    connected PipelineInputs.
    """

    def __init__(self, owner: "Operator", name: str):
        self.owner = owner
        self.name = name
        self.downstream_inputs: list[PipelineInput] = []

    def _spawn_input(self, owner: "Operator", name: str) -> PipelineInput:
        input = PipelineInput(self, owner, name)
        self.downstream_inputs.append(input)
        return input


class OperatorInputs:
    """
    A collection of all PipelineInputs for an Operator instance (i.e. a Task).
    """

    def __init__(
        self, owner: "Operator", **input_descriptors: tuple[Type[PipelineOutput], PipelineOutput]
    ):
        """
        input_descriptors is a dict of input name -> (required_upstream_output_type, upstream_output)
        We have that required_upstream_output_type so we can do runtime validation that each given
        output is of the correct type for the input it's hooked up to.
        """
        self.inputs: set[PipelineInput] = set()
        for name, (required_upstream_output_type, upstream_output) in input_descriptors.items():
            if not isinstance(upstream_output, required_upstream_output_type):
                raise ValueError(
                    f"Input {name} must be a {required_upstream_output_type.__name__}, got {upstream_output.__class__.__name__}"
                )
            self.inputs.add(upstream_output._spawn_input(owner, name))

    def _to_dict(self, id_for_task: dict) -> dict[str, str]:
        d: dict[str, str] = {}
        for input in self.inputs:
            d |= input._to_dict(id_for_task)
        return d


T = TypeVar("T", bound="OperatorOutputs")


class OperatorOutputs(ABC):
    """
    A collection of all PipelineOutputs for an Operator instance (i.e. a Task). Must be subclassed,
    and the subclass must also be a dataclass whose fields are all PipelineOutput subclasses. Then
    that subclass should be instantiated with `_instantiate_for`. Sounds a little complicated,
    perhaps, but it's not bad. See the existing subclasses in `./operators.py` for examples.
    """

    @classmethod
    def _instantiate_for(cls: type[T], owner: "Operator") -> T:
        # create an instance with all fields instantiated with the given owner, and named by the
        # field name.
        # Also validate here that we are a dataclass, and all our fields are PipelineOutput types.
        # Would love to get this done in the type system, but I think it's impossible, so this is
        # the next best thing.
        if not is_dataclass(cls):
            raise TypeError(f"'{cls.__name__}' must be a dataclass")
        outputs = {}
        for field in fields(cls):
            assert not isinstance(field.type, str)
            if not issubclass(field.type, PipelineOutput):
                raise TypeError(
                    f"Field '{field.name}' in '{cls.__name__}' must be a subclass of PipelineOutput"
                )
            outputs[field.name] = field.type(owner, field.name)
        return cls(**outputs)


TOutputs = TypeVar("TOutputs", bound=OperatorOutputs)


class Operator(Generic[TOutputs], ABC):
    def __init__(
        self,
        task_name: str | None,
        params: dict,
        inputs: OperatorInputs,
        outputs: TOutputs,
    ):
        self._operator_name = self.__class__.__name__
        self._task_name = task_name if task_name is not None else self._operator_name
        self._params = params
        self._inputs = inputs
        self.outputs = outputs
        ensure_yamlizable(self._params_dict()[0], "Operator parameters")

    def _to_dict(self, id_for_task: dict) -> tuple[dict, list[PipelineParameter]]:
        params, params_list = self._params_dict()
        d = {
            "name": self._task_name,
            "operator": self._operator_name,
            "params": params,
            "inputs": self._inputs._to_dict(id_for_task),
        }
        return d, params_list

    def _params_dict(self) -> tuple[dict, list[PipelineParameter]]:
        d = {}
        params = []
        for name, value in self._params.items():
            if hasattr(value, "_to_pipeline_dict"):
                d[name], downstream_params = value._to_pipeline_dict()
                params.extend(downstream_params)
            else:
                d[name] = value
        return d, params

    def __str__(self) -> str:
        return f'{self._operator_name}(name="{self._task_name}")'


@experimental
class Pipeline:
    def __init__(self, name: str, tasks: list[Operator]):
        self.name = name
        self.tasks = tasks

    def to_yaml(self) -> str:
        return yaml.safe_dump(self._to_dict())

    def _to_dict(self) -> dict:
        id_for_task = self._assign_ids_to_tasks()
        tasks = {}
        params = []
        for task in id_for_task.keys():
            task_dict, referenced_params = task._to_dict(id_for_task)
            tasks[id_for_task[task]] = task_dict
            params.extend(referenced_params)

        d = {
            "lc_pipeline": {
                "schema_version": 1,
                "name": self.name,
                "params": self._pipeline_params_dict(params),
                "tasks": tasks,
            }
        }
        ensure_yamlizable(d, "Pipeline")
        return d

    def _assign_ids_to_tasks(self) -> dict[Operator, str]:
        return {task: f"t{i + 1}-{task._operator_name}" for i, task in enumerate(self.tasks)}

    def _pipeline_params_dict(self, params: list[PipelineParameter]) -> dict:
        d: dict[str, dict] = {}
        for p in params:
            if p.name in d and d[p.name]["type"] != p.type:
                raise ValueError(
                    f'PipelineParameter "{p.name}" used with multiple types: {d[p.name]["type"]} != {p.type}'
                )
            d[p.name] = {"type": p.type}
        return d
