# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

"""Configuration dataclass for Vega robot sensors.

This module defines the VegaSensorsConfig dataclass which specifies the default
configurations for all sensors on the Vega robot, including cameras, IMUs,
LiDAR and ultrasonic sensors.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from .cameras import GeminiCameraConfig, RGBCameraConfig
from .imu import GeminiIMUConfig, NineAxisIMUConfig
from .lidar import RPLidarConfig
from .ultrasonic import UltraSonicConfig


def _make_rgb_camera(topic: str, name: str) -> Callable[[], RGBCameraConfig]:
    """Helper function to create RGB camera config factory.

    Args:
        topic: Camera topic name
        name: Camera instance name

    Returns:
        Factory function that creates an RGBCameraConfig
    """
    return lambda: RGBCameraConfig(
        topic=f"camera/base/{topic}", name=f"base_{name}_camera"
    )


@dataclass
class VegaSensorsConfig:
    """Configuration for all sensors on the Vega robot.

    Contains default configurations for:
    - Head camera (Gemini)
    - Base cameras (RGB) - left, right, front, back
    - IMUs - base (9-axis) and head (Gemini)
    - LiDAR
    - Ultrasonic sensors
    """

    head_camera: GeminiCameraConfig = field(default_factory=GeminiCameraConfig)
    base_left_camera: RGBCameraConfig = field(
        default_factory=_make_rgb_camera("left", "left")
    )
    base_right_camera: RGBCameraConfig = field(
        default_factory=_make_rgb_camera("right", "right")
    )
    base_front_camera: RGBCameraConfig = field(
        default_factory=_make_rgb_camera("front", "front")
    )
    base_back_camera: RGBCameraConfig = field(
        default_factory=_make_rgb_camera("back", "back")
    )
    base_imu: NineAxisIMUConfig = field(default_factory=NineAxisIMUConfig)
    head_imu: GeminiIMUConfig = field(default_factory=GeminiIMUConfig)
    lidar: RPLidarConfig = field(default_factory=RPLidarConfig)
    ultrasonic: UltraSonicConfig = field(default_factory=UltraSonicConfig)
