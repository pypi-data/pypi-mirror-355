# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

"""Nine-Axis IMU sensor implementation using Zenoh subscriber."""

import numpy as np
import zenoh

from dexcontrol.utils.subscribers.imu import IMUSubscriber


class NineAxisIMUSensor:
    """Nine-Axis IMU sensor using Zenoh subscriber.

    This sensor provides 9-axis IMU data including acceleration, angular velocity,
    orientation, and magnetometer data using the IMUSubscriber for efficient data handling.
    """

    def __init__(
        self,
        configs,
        zenoh_session: zenoh.Session,
    ) -> None:
        """Initialize the Nine-Axis IMU sensor.

        Args:
            topic: Zenoh topic to subscribe to for IMU data.
            zenoh_session: Active Zenoh session for communication.
            name: Name for the sensor instance.
            enable_fps_tracking: Whether to track and log FPS metrics.
        """
        self._name = configs.name

        # Create the IMU subscriber
        self._subscriber = IMUSubscriber(
            topic=configs.topic,
            zenoh_session=zenoh_session,
            name=f"{self._name}_subscriber",
            enable_fps_tracking=configs.enable_fps_tracking,
            fps_log_interval=configs.fps_log_interval,
        )


    def shutdown(self) -> None:
        """Shutdown the IMU sensor."""
        self._subscriber.shutdown()

    def is_active(self) -> bool:
        """Check if the IMU sensor is actively receiving data.

        Returns:
            True if receiving data, False otherwise.
        """
        return self._subscriber.is_active()

    def wait_for_active(self, timeout: float = 5.0) -> bool:
        """Wait for the IMU sensor to start receiving data.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if sensor becomes active, False if timeout is reached.
        """
        return self._subscriber.wait_for_active(timeout)

    def get_obs(self, obs_keys: list[str] | None = None) -> dict[str, np.ndarray] | None:
        """Get observation data for the Nine-Axis IMU sensor.

        Args:
            obs_keys: List of observation keys to retrieve. If None, returns all available data.
                     Valid keys: ['ang_vel', 'acc', 'mag', 'quat']

        Returns:
            Dictionary with observation data including all IMU measurements.
        """
        if obs_keys is None:
            obs_keys = ['ang_vel', 'acc', 'mag', 'quat']

        data = self._subscriber.get_latest_data()
        if data is None:
            return None

        obs_out = {}
        for key in obs_keys:
            if key == 'ang_vel':
                obs_out[key] = data['angular_velocity']
            elif key == 'acc':
                obs_out[key] = data['acceleration']
            elif key == 'mag':
                obs_out[key] = data['magnetometer']
            elif key == 'quat':
                obs_out[key] = data['orientation']
            else:
                raise ValueError(f"Invalid observation key: {key}")

        return obs_out

    def get_acceleration(self) -> np.ndarray | None:
        """Get the latest linear acceleration.

        Returns:
            Linear acceleration [x, y, z] in m/s² if available, None otherwise.
        """
        return self._subscriber.get_acceleration()

    def get_angular_velocity(self) -> np.ndarray | None:
        """Get the latest angular velocity.

        Returns:
            Angular velocity [x, y, z] in rad/s if available, None otherwise.
        """
        return self._subscriber.get_angular_velocity()

    def get_orientation(self) -> np.ndarray | None:
        """Get the latest orientation quaternion.

        Returns:
            Orientation quaternion [x, y, z, w] if available, None otherwise.
        """
        return self._subscriber.get_orientation()

    def get_magnetometer(self) -> np.ndarray | None:
        """Get the latest magnetometer reading.

        Returns:
            Magnetic field [x, y, z] in µT if available, None otherwise.
        """
        return self._subscriber.get_magnetometer()

    @property
    def fps(self) -> float:
        """Get the current FPS measurement.

        Returns:
            Current frames per second measurement.
        """
        return self._subscriber.fps

    @property
    def name(self) -> str:
        """Get the IMU name.

        Returns:
            IMU name string.
        """
        return self._name
