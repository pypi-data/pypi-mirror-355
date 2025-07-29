# Copyright 2023-2024 Luminary Cloud, Inc. All Rights Reserved.
import dataclasses as dc
from luminarycloud.types import Vector3, Vector3Like


@dc.dataclass
class Plane:
    """
    This class defines a plane.

    .. warning:: This feature is experimental and may change or be removed in the future.

    """

    origin: Vector3Like = dc.field(default_factory=lambda: Vector3(x=0, y=0, z=0))
    """A point defined on the plane. Default: [0,0,0]."""
    normal: Vector3Like = dc.field(default_factory=lambda: Vector3(x=1, y=0, z=0))
    """The vector orthogonal to the  plane. Default: [0,1,0]"""


@dc.dataclass
class Box:
    """
    This class defines a box used for filter such as box clip.

    .. warning:: This feature is experimental and may change or be removed in the future.

    """

    center: Vector3Like = dc.field(default_factory=lambda: Vector3(x=0, y=0, z=0))
    """A point defined at the center of the box. Default: [0,0,0]."""
    lengths: Vector3Like = dc.field(default_factory=lambda: Vector3(x=1, y=1, z=1))
    """The the legnths of each side of the box. Default: [1,1,1]"""
    angles: Vector3Like = dc.field(default_factory=lambda: Vector3(x=0, y=0, z=0))
    """
    The rotation of the box specified in Euler angles (degrees) and applied
    in XYZ ordering. Default: [0,0,0]
    """
