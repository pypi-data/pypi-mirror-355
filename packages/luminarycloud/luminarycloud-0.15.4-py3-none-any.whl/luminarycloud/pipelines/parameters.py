# Copyright 2025 Luminary Cloud, Inc. All Rights Reserved.
from .core import PipelineParameter


class StringPipelineParameter(PipelineParameter):
    """
    A String Pipeline Parameter can replace a hard-coded string in Pipeline operator arguments to
    allow its value to be set when the Pipeline is invoked.
    """

    def _type(self) -> str:
        return "string"


class FloatPipelineParameter(PipelineParameter):
    """
    A Float Pipeline Parameter can replace a hard-coded float in Pipeline operator arguments to
    allow its value to be set when the Pipeline is invoked.
    """

    def _type(self) -> str:
        return "float"


class IntPipelineParameter(PipelineParameter):
    """
    An Int Pipeline Parameter can replace a hard-coded int in Pipeline operator arguments to
    allow its value to be set when the Pipeline is invoked.
    """

    def _type(self) -> str:
        return "int"


class BoolPipelineParameter(PipelineParameter):
    """
    A Bool Pipeline Parameter can replace a hard-coded bool in Pipeline operator arguments to
    allow its value to be set when the Pipeline is invoked.
    """

    def _type(self) -> str:
        return "bool"
