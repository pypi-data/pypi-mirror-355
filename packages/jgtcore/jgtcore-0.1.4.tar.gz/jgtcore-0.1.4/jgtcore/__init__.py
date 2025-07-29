#!/usr/bin/env python3

"""
jgtcore - Core library functions extracted from jgtutils

This module provides the core configuration, settings, and utility functions
from jgtutils without CLI dependencies, making them suitable for use in
other libraries and applications.

Main Functions:
- Configuration: readconfig(), get_config(), get_config_value()
- Settings: load_settings(), get_settings(), get_setting()
- Environment: setup_environment(), export_env_if_any()
- Utilities: str_to_datetime(), is_market_open(), print_exception()
- Trading: read_fx_str_from_config(), is_demo_mode()
"""

from .core import (  # Core configuration functions; Simple API wrappers; Environment helpers; Utility functions; Trading helpers; Helper functions for advanced use
    dt_from_last_week_as_datetime,
    dt_from_last_week_as_string_fxformat,
    export_env_if_any,
    get_config,
    get_config_value,
    get_setting,
    get_settings,
    is_demo_mode,
    is_market_open,
    load_arg_default_from_settings,
    load_arg_default_from_settings_if_exist,
    load_arg_from_jgt_env,
    load_settings,
    print_exception,
    read_fx_str_from_config,
    readconfig,
    setup_environment,
    str_to_datetime,
    update_settings,
)

__version__ = "0.1.4"
__author__ = "JGWill"
__description__ = "Core library functions extracted from jgtutils"

# Export the main functions that external packages are likely to use
__all__ = [
    # Configuration functions
    "readconfig",
    "load_settings",
    "get_settings",
    # Simple API wrappers
    "get_config",
    "get_setting",
    "setup_environment",
    "get_config_value",
    "is_demo_mode",
    # Environment helpers
    "load_arg_from_jgt_env",
    "load_arg_default_from_settings",
    "export_env_if_any",
    # Utility functions
    "str_to_datetime",
    "print_exception",
    "is_market_open",
    "dt_from_last_week_as_datetime",
    "dt_from_last_week_as_string_fxformat",
    # Trading helpers
    "read_fx_str_from_config",
    # Helper functions
    "update_settings",
    "load_arg_default_from_settings_if_exist",
]
