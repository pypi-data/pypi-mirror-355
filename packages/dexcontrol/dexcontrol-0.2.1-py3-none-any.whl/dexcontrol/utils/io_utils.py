# Copyright (c) 2025 Dexmate CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 with Commons Clause License
# Condition v1.0 [see LICENSE for details].

from typing import Any

from loguru import logger


def print_dict(d: dict[str, Any], indent: int = 0) -> None:
    """Print a nested dictionary with nice formatting.

    Recursively prints dictionary contents with proper indentation.

    Args:
        d: Dictionary to print.
        indent: Current indentation level in spaces.
    """
    indent_str = " " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            logger.info(f"{indent_str}{key}:")
            print_dict(value, indent + 4)
        else:
            logger.info(f"{indent_str}{key}: {value}")
