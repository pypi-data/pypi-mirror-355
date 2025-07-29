#!/usr/bin/env python3

# Copyright 2019 Gehtsoft USA LLC
# Copyright 2023 JGWill (extended/variations)

# Licensed under the license derived from the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# You may obtain a copy of the License at

# http://fxcodebase.com/licenses/open-source/license.html

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
jgtcore.core - Core library functions extracted from jgtutils
Provides configuration, settings, and utility functions without CLI dependencies.
"""

import json

# Optional YAML support - graceful fallback to JSON-only if not available
try:
    import ruamel.yaml

    yaml = ruamel.yaml.YAML()
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False

import os
import sys
import traceback
from datetime import datetime, time, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

# Global variables for caching
settings: Dict[str, Any] = {}
_JGT_CONFIG_JSON_SECRET: Optional[str] = None

# Core Configuration Functions


def _load_settings_from_path(path: str) -> Dict[str, Any]:
    """Load settings from a JSON file path."""
    if os.path.exists(path):
        with open(path, "r") as f:
            loaded_data = json.load(f)
            return loaded_data
    return {}


def _load_settings_from_path_yaml(
    path: str, key: Optional[str] = None
) -> Dict[str, Any]:
    """Load settings from a YAML file path, optionally extracting a specific key."""
    if not HAS_YAML:
        # YAML not available, skip YAML file loading
        return {}

    if os.path.exists(path):
        with open(path, "r") as f:
            if key is not None:
                try:
                    yaml_value = yaml.load(f)
                except yaml.YAMLError as exc:
                    print(exc)
                if yaml_value is not None and key in yaml_value:
                    return yaml_value[key]
                else:
                    return {}
            yaml_data = yaml.load(f)
            if yaml_data is None:
                return {}
            return yaml_data
    return {}


def update_settings(
    old_settings: Dict[str, Any],
    new_settings: Dict[str, Any],
    keys: list = ["patterns"],
) -> None:
    """Update old_settings with new_settings, handling special keys separately."""
    # if our old settings has a key in our keys list, then we will update it on their own
    # (meaning we will not merge it directly but update it independently)
    for key in keys:
        if key in old_settings:
            if new_settings is not None and key in new_settings:
                test_if_key_not_none = new_settings[key]
                if test_if_key_not_none is not None:
                    old_settings[key].update(new_settings[key])
                # remove the key from the new settings
                new_settings.pop(key)
    if new_settings is not None:
        old_settings.update(new_settings)


def _settings_loaded(_settings: Dict[str, Any]) -> None:
    """Hook called when settings are loaded. Override for custom behavior."""
    return


def load_settings(
    custom_path: Optional[str] = None, old: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load settings from multiple locations in order of precedence.

    Args:
        custom_path: Optional custom path to settings file
        old: Existing settings to merge with

    Returns:
        Merged settings dictionary
    """
    system_settings_path = os.path.join("/etc", "jgt", "settings.json")
    home_settings_path = os.path.join(os.path.expanduser("~"), ".jgt", "settings.json")
    current_settings_path = os.path.join(os.getcwd(), ".jgt", "settings.json")
    yaml_current_settings_path = os.path.join(os.getcwd(), ".jgt", "settings.yml")
    jgt_yaml_current_settings_path = os.path.join(os.getcwd(), "jgt.yml")
    jubook_jgt_yaml_current_settings_path = os.path.join(os.getcwd(), "_config.yml")

    _settings = {}
    if old is not None:
        _settings = old

    # Load system settings
    system_settings = _load_settings_from_path(system_settings_path)
    update_settings(_settings, system_settings)

    # Load from env JGT_SETTINGS_SYSTEM if exists
    if "JGT_SETTINGS_SYSTEM" in os.environ:
        env_settings_system = json.loads(os.environ["JGT_SETTINGS_SYSTEM"])
        update_settings(_settings, env_settings_system)

    # Load user settings
    user_settings = _load_settings_from_path(home_settings_path)
    update_settings(_settings, user_settings)

    # Load from env JGT_SETTINGS or JGT_SETTINGS_USER if exists
    if "JGT_SETTINGS" in os.environ:
        env_settings_user = json.loads(os.environ["JGT_SETTINGS"])
        update_settings(_settings, env_settings_user)

    if "JGT_SETTINGS_USER" in os.environ:
        env_settings_user = json.loads(os.environ["JGT_SETTINGS_USER"])
        update_settings(_settings, env_settings_user)

    # Load current directory settings
    current_settings = _load_settings_from_path(current_settings_path)
    update_settings(_settings, current_settings)

    current_settings_yaml = _load_settings_from_path_yaml(yaml_current_settings_path)
    update_settings(_settings, current_settings_yaml)

    jubook_jgt_current_settings_yaml = _load_settings_from_path_yaml(
        jubook_jgt_yaml_current_settings_path, key="jgt"
    )
    update_settings(_settings, jubook_jgt_current_settings_yaml)

    jgt_current_settings_yaml = _load_settings_from_path_yaml(
        jgt_yaml_current_settings_path
    )
    update_settings(_settings, jgt_current_settings_yaml)

    # Load custom settings if provided
    if custom_path is not None and custom_path != "":
        custom_settings = {}
        if ".json" in custom_path:
            custom_settings = _load_settings_from_path(custom_path)
        else:
            if ".yml" in custom_path:
                custom_settings = _load_settings_from_path_yaml(custom_path)
        update_settings(_settings, custom_settings)

    # Load process-level settings from environment
    if "JGT_SETTINGS_PROCESS" in os.environ:
        env_settings_process = json.loads(os.environ["JGT_SETTINGS_PROCESS"])
        update_settings(_settings, env_settings_process)

    _settings_loaded(_settings)

    return _settings


def get_settings(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get cached settings, loading them if necessary.

    Args:
        custom_path: Optional custom path to settings file

    Returns:
        Settings dictionary
    """
    global settings
    if settings is None or len(settings) == 0:
        settings = load_settings(custom_path=custom_path)
    return settings


def load_arg_default_from_settings(
    argname: str,
    default_value: Any,
    alias: Optional[str] = None,
    from_jgt_env: bool = False,
    exclude_env_alias: bool = False,
) -> Any:
    """
    Load argument default value from settings.

    Args:
        argname: Argument name to look up
        default_value: Default value if not found
        alias: Alternative name to check
        from_jgt_env: Whether to load from JGT environment
        exclude_env_alias: Whether to exclude alias when loading from env

    Returns:
        Setting value or default
    """
    global settings
    if settings is None or len(settings) == 0:
        settings = load_settings()

    _value = settings.get(argname, default_value)
    if alias is not None and _value == default_value:
        _value = settings.get(alias, default_value)  # try alias might be used

    if from_jgt_env:
        _alias = None if exclude_env_alias else alias
        _value = load_arg_from_jgt_env(argname, _alias)

    return _value


def load_arg_from_jgt_env(argname: str, alias: Optional[str] = None) -> Optional[str]:
    """
    Load argument value from JGT environment variables.

    Args:
        argname: Argument name to look up
        alias: Alternative name to check

    Returns:
        Environment variable value or None
    """
    _value = None
    # Note: load_env() is from jgtenv, but we'll just check the environment directly
    if argname in os.environ:
        _value = os.getenv(argname, None)
    if alias is not None and _value is None:
        _value = os.getenv(alias, None)
    return _value


def load_arg_default_from_settings_if_exist(
    argname: str, alias: Optional[str] = None
) -> Optional[Any]:
    """
    Load argument default from settings only if it exists.

    Args:
        argname: Argument name to look up
        alias: Alternative name to check

    Returns:
        Setting value or None
    """
    global settings
    if settings is None or len(settings) == 0:
        settings = load_settings()

    _value = settings.get(argname, None)
    if alias is not None and _value == None:
        _value = settings.get(alias, None)  # try alias might be used
    return _value


def export_env_if_any(config: Dict[str, Any]) -> None:
    """Export certain config values to environment variables if they exist."""
    # if has a key : "keep_bid_ask" and if yes and set to "true", export an env variable "JGT_KEEP_BID_ASK" to "1"
    if "keep_bid_ask" in config and config["keep_bid_ask"] == True:
        os.environ["JGT_KEEP_BID_ASK"] = "1"


def _set_demo_credential(config: Dict[str, Any], demo: bool = False) -> None:
    """Set demo credentials in config if demo mode is enabled."""
    if demo:
        config["user_id"] = config["user_id_demo"]
        config["password"] = config["password_demo"]
        config["account"] = config["account_demo"]
        config["connection"] = "Demo"


def readconfig(
    json_config_str: Optional[str] = None,
    config_file: str = "config.json",
    export_env: bool = False,
    config_file_path_env_name: str = "JGT_CONFIG_PATH",
    config_values_env_name: str = "JGT_CONFIG",
    force_read_json: bool = False,
    demo: bool = False,
    use_demo_json_config: bool = False,
) -> Dict[str, Any]:
    """
    Read configuration from various sources.

    Args:
        json_config_str: JSON string containing config
        config_file: Config file name
        export_env: Whether to export config to environment variables
        config_file_path_env_name: Environment variable name for config file path
        config_values_env_name: Environment variable name for config JSON
        force_read_json: Force reading from default JSON file
        demo: Whether to use demo credentials
        use_demo_json_config: Whether to use demo-specific config file

    Returns:
        Configuration dictionary
    """
    global _JGT_CONFIG_JSON_SECRET

    try:
        home_dir = os.path.expanduser("~")
    except:
        home_dir = os.environ["HOME"]
    if home_dir == "":
        home_dir = os.environ["HOME"]

    # demo_config are assumed to be $HOME/.jgt/config_demo.json
    if demo and use_demo_json_config:
        config_file = os.path.join(home_dir, ".jgt/config_demo.json")
        # check if exist, advise and raise exception if not
        if not os.path.exists(config_file):
            print(
                f"Configuration not found. create : {config_file} or we will try to use the _demo in the usual config.json"
            )
            config = readconfig(force_read_json=True)
            _set_demo_credential(config, demo)
            return config

    # force_read_json are assumed to be $HOME/.jgt/config.json
    if force_read_json:
        config_file = os.path.join(home_dir, ".jgt/config.json")
        # check if exist, advise and raise exception if not
        if not os.path.exists(config_file):
            raise Exception(f"Configuration not found. create : {config_file})")
        # load and return config
        with open(config_file, "r") as f:
            config = json.load(f)
            if export_env:
                export_env_if_any(config)
            _set_demo_credential(config, demo)
            return config

    # Try reading config from JSON string first
    if json_config_str is not None:
        config = json.loads(json_config_str)
        _JGT_CONFIG_JSON_SECRET = json_config_str
        if export_env:
            export_env_if_any(config)
        _set_demo_credential(config, demo)
        return config

    # Try cached config
    if _JGT_CONFIG_JSON_SECRET is not None:
        config = json.loads(_JGT_CONFIG_JSON_SECRET)
        if export_env:
            export_env_if_any(config)
        _set_demo_credential(config, demo)
        return config

    config = None

    # if file does not exist try set the path to the file in the HOME
    if not os.path.exists(config_file):
        config_file = os.path.join(home_dir, config_file)

    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            if export_env:
                export_env_if_any(config)
            _set_demo_credential(config, demo)
            return config
    else:
        config_file = os.path.join(home_dir, config_file)
        if os.path.isfile(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        else:
            # If config file still not found, try reading from environment variable
            config_json_str = os.getenv("JGT_CONFIG_JSON_SECRET")
            if config_json_str:
                config = json.loads(config_json_str)
                if export_env:
                    export_env_if_any(config)
                _set_demo_credential(config, demo)
                return config

    # if file dont exist, try loading from env var JGT_CONFIG
    if not os.path.exists(config_file):
        config_json_str = os.getenv(config_values_env_name)

        if config_json_str:
            config = json.loads(config_json_str)
            if export_env:
                export_env_if_any(config)
        else:
            # if not found, try loading from env var JGT_CONFIG_PATH
            config_file = os.getenv(config_file_path_env_name)
            if config_file:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    if export_env:
                        export_env_if_any(config)

    # Read config file
    if config is None:
        if config_file is not None and os.path.exists(config_file):
            with open(config_file, "r") as file:
                config = json.load(file)

    if config is None:
        # Last attempt to read
        try:
            another_config = "config.json"
            if not os.path.exists(another_config):
                another_config = os.path.join(
                    os.path.expanduser("~"), ".jgt", "config.json"
                )

            if not os.path.exists(another_config):
                another_config = "/etc/jgt/config.json"
            with open(another_config, "r") as file:
                config = json.load(file)
        except:
            pass

        if config is None:
            try:
                with open("/home/jgi/.jgt/config.json", "r") as file:
                    config = json.load(file)
            except:
                pass
        if config is None:
            try:
                with open("/etc/jgt/config.json", "r") as file:
                    config = json.load(file)
            except:
                pass

        if config is None:
            raise Exception(
                f"Configuration not found. Please provide a config file or set the JGT_CONFIG environment variable to the JSON config string. (config_file={config_file})"
            )

    if export_env:
        export_env_if_any(config)
    _set_demo_credential(config, demo)
    return config


# Utility Functions


def str_to_datetime(date_str: str) -> Optional[datetime]:
    """
    Convert string to datetime using multiple format attempts.

    Args:
        date_str: Date string to parse

    Returns:
        datetime object or None if parsing fails
    """
    formats = [
        "%m.%d.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def print_exception(exception: Exception) -> None:
    """Print exception with traceback."""
    print("Exception: {0}\n{1}".format(exception, traceback.format_exc()))


def is_market_open(
    current_time: Optional[datetime] = None,
    exit_cli_if_closed: bool = False,
    market_closed_callback: Optional[callable] = None,
) -> bool:
    """
    Check if forex market is currently open.

    Args:
        current_time: Time to check (defaults to now)
        exit_cli_if_closed: Whether to exit if market is closed (not recommended for library use)
        market_closed_callback: Callback to call if market is closed

    Returns:
        True if market is open
    """
    if current_time is None:
        current_time = datetime.utcnow()

    # Define market open and close times
    market_open_time = time(21, 0)  # 21:00 UTC
    market_close_time = time(21, 15)  # 21:15 UTC

    # Get the current day of the week (0=Monday, 6=Sunday)
    current_day = current_time.weekday()

    current_time_utc = current_time.time()
    # Check if the market is open
    if current_day == 6:  # Sunday
        if current_time_utc >= market_open_time:
            return True
    elif current_day == 4:  # Friday
        if current_time_utc < market_close_time:
            return True
    elif 0 <= current_day < 4:  # Monday to Thursday
        return True

    if market_closed_callback is not None:
        market_closed_callback()
    if exit_cli_if_closed:
        print("Market is closed.")
        sys.exit(1)  # Simplified exit code for library use
    return False


def dt_from_last_week_as_datetime() -> datetime:
    """Get datetime from last week."""
    today = datetime.now()
    last_week = today - timedelta(days=7)
    return last_week


def dt_from_last_week_as_string_fxformat() -> str:
    """Get datetime from last week as FX format string."""
    last_week = dt_from_last_week_as_datetime()
    _str = last_week.strftime("%m.%d.%Y")
    return _str + " 00:00:00"


def read_fx_str_from_config(demo: bool = False) -> Tuple[str, str, str, str, str]:
    """
    Read FX connection parameters from config.

    Args:
        demo: Whether to use demo credentials

    Returns:
        Tuple of (user_id, password, url, connection, account)
    """
    config = readconfig(demo=demo)
    if (
        config["connection"] == "Real" and demo
    ):  # Make sure we have our demo credentials
        _set_demo_credential(config, True)
    str_user_id = config["user_id"]
    str_password = config["password"]
    str_url = config["url"]
    str_connection = "Real" if not demo else "Demo"
    str_account = config["account"]
    return str_user_id, str_password, str_url, str_connection, str_account


# Simple API wrappers for external packages


def get_config(demo: bool = False, export_env: bool = False) -> Dict[str, Any]:
    """
    Simple configuration loader for external packages.

    Args:
        demo: Whether to use demo credentials
        export_env: Whether to export config to environment variables

    Returns:
        Configuration dictionary
    """
    return readconfig(demo=demo, export_env=export_env)


def get_setting(
    key: str, default: Any = None, custom_path: Optional[str] = None
) -> Any:
    """
    Get a single setting value.

    Args:
        key: Setting key to retrieve
        default: Default value if key not found
        custom_path: Optional custom path to settings file

    Returns:
        Setting value or default
    """
    settings = get_settings(custom_path=custom_path)
    return settings.get(key, default)


def setup_environment(
    demo: bool = False, custom_settings_path: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    One-call setup for external packages.
    Sets up configuration and settings, exports environment variables.

    Args:
        demo: Whether to use demo credentials
        custom_settings_path: Optional custom path to settings file

    Returns:
        Tuple of (config_dict, settings_dict)
    """
    config = readconfig(demo=demo, export_env=True)
    settings = get_settings(custom_path=custom_settings_path)
    return config, settings


def get_config_value(key: str, default: Any = None, demo: bool = False) -> Any:
    """
    Get a single configuration value.

    Args:
        key: Configuration key to retrieve
        default: Default value if key not found
        demo: Whether to use demo credentials

    Returns:
        Configuration value or default
    """
    config = readconfig(demo=demo)
    return config.get(key, default)


def is_demo_mode() -> bool:
    """
    Check if running in demo mode based on current configuration.

    Returns:
        True if demo mode is active
    """
    try:
        config = readconfig()
        return config.get("connection", "").lower() == "demo"
    except:
        return False
