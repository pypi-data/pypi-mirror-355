# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

"""Utility for resetting Orbbec camera USB connection."""

import os
import sys
import time

import pyudev
from loguru import logger

# Orbbec vendor ID constant
_ORBBEC_VENDOR_ID = "2bc5"


def check_root() -> None:
    """Verify the script is running with root privileges.

    Exits the program if not running as root.
    """
    if os.geteuid() != 0:
        logger.error("This script must be run as root (sudo). Exiting...")
        logger.info("Run with: sudo $(which python) reset_orbbec_camera_usb.py")
        sys.exit(1)


def reset_orbbec() -> bool:
    """Reset the USB connection for an Orbbec camera.

    Simulates unplugging and replugging the device by toggling the USB
    authorization state.

    Returns:
        bool: True if camera was found and reset successfully, False otherwise.
    """
    # Check for root privileges first
    check_root()

    # Initialize pyudev
    context = pyudev.Context()

    # Find Orbbec device
    for device in context.list_devices(subsystem="usb"):
        if device.properties.get("ID_VENDOR_ID") == _ORBBEC_VENDOR_ID:
            return _reset_device(device)

    logger.warning("Orbbec camera not found")
    return False


def _reset_device(device: pyudev.Device) -> bool:
    """Reset a specific USB device.

    Args:
        device: pyudev Device object to reset

    Returns:
        bool: True if reset was successful, False otherwise
    """
    # Get the parent device (USB port)
    port = device.find_parent("usb", "usb_device")

    if port is None:
        logger.warning("Could not find parent USB device")
        return False

    # Construct path to authorized file
    path = os.path.join(port.sys_path, "authorized")

    if not os.path.exists(path):
        logger.warning(f"Authorize file not found at: {path}")
        return False

    try:
        # Simulate unplug
        with open(path, "w") as f:
            f.write("0")
        logger.info("USB device deauthorized")

        # Wait a moment for the system to process
        time.sleep(1)

        # Simulate plug
        with open(path, "w") as f:
            f.write("1")

        logger.info(f"Orbbec camera reset successfully. Path: {path}")
        return True
    except IOError as e:
        logger.error(f"Failed to reset device: {e}")
        return False


if __name__ == "__main__":
    reset_orbbec()
