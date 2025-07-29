#!/usr/bin/env python3

"""
Test script for jgtcore library

Tests the core functionality extracted from jgtutils
"""

import json
import os
import sys
import tempfile
from datetime import datetime

# Add jgtcore to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core


def test_str_to_datetime():
    """Test string to datetime conversion."""
    print("Testing str_to_datetime...")

    test_cases = [
        ("2024-01-15 10:30:00", True),
        ("01.15.2024 10:30:00", True),
        ("2024/01/15", True),
        ("invalid-date", False),
        ("", False),
    ]

    for date_str, should_succeed in test_cases:
        result = core.str_to_datetime(date_str)
        if should_succeed:
            assert result is not None, f"Expected {date_str} to parse successfully"
            assert isinstance(
                result, datetime
            ), f"Expected datetime object for {date_str}"
            print(f"   ✓ {date_str} -> {result}")
        else:
            assert result is None, f"Expected {date_str} to fail parsing"
            print(f"   ✓ {date_str} -> None (as expected)")


def test_market_open():
    """Test market open functionality."""
    print("Testing is_market_open...")

    # Test with current time
    result = core.is_market_open()
    print(f"   Current market status: {'Open' if result else 'Closed'}")

    # Test with specific times (without exit behavior)
    test_time = datetime(2024, 1, 15, 10, 0)  # Monday 10:00 UTC
    result = core.is_market_open(test_time)
    print(f"   Monday 10:00 UTC: {'Open' if result else 'Closed'}")


def test_datetime_helpers():
    """Test datetime helper functions."""
    print("Testing datetime helpers...")

    last_week_dt = core.dt_from_last_week_as_datetime()
    last_week_str = core.dt_from_last_week_as_string_fxformat()

    assert isinstance(last_week_dt, datetime), "Expected datetime object"
    assert isinstance(last_week_str, str), "Expected string"
    assert "00:00:00" in last_week_str, "Expected time suffix in FX format"

    print(f"   ✓ Last week datetime: {last_week_dt}")
    print(f"   ✓ Last week FX format: {last_week_str}")


def test_settings_with_temp_file():
    """Test settings loading with temporary files."""
    print("Testing settings loading...")

    # Create temporary settings file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_settings = {"instrument": "GBP/USD", "timeframe": "M15", "test_value": 42}
        json.dump(test_settings, f)
        temp_path = f.name

    try:
        # Test loading settings from custom path
        settings = core.load_settings(custom_path=temp_path)

        assert "instrument" in settings, "Expected instrument in settings"
        assert settings["instrument"] == "GBP/USD", "Expected correct instrument value"
        assert settings["timeframe"] == "M15", "Expected correct timeframe value"
        assert settings["test_value"] == 42, "Expected correct test value"

        print(f"   ✓ Loaded settings: {len(settings)} keys")
        print(f"   ✓ Instrument: {settings['instrument']}")
        print(f"   ✓ Timeframe: {settings['timeframe']}")

        # Test get_settings caching
        cached_settings = core.get_settings()
        print(f"   ✓ Cached settings: {len(cached_settings)} keys")

    finally:
        # Clean up
        os.unlink(temp_path)


def test_config_loading():
    """Test configuration loading."""
    print("Testing configuration loading...")

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        test_config = {
            "url": "https://test.example.com",
            "user_id": "test_user",
            "password": "test_pass",
            "account": "test_account",
            "connection": "Demo",
            "user_id_demo": "demo_user",
            "password_demo": "demo_pass",
            "account_demo": "demo_account",
        }
        json.dump(test_config, f)
        temp_path = f.name

    try:
        # Test direct JSON string loading
        config_str = json.dumps(test_config)
        config = core.readconfig(json_config_str=config_str)

        assert config["url"] == "https://test.example.com", "Expected correct URL"
        assert config["user_id"] == "test_user", "Expected correct user ID"

        print(f"   ✓ Config from JSON string: {len(config)} keys")

        # Test demo mode
        demo_config = core.readconfig(json_config_str=config_str, demo=True)
        assert demo_config["connection"] == "Demo", "Expected demo connection"
        assert demo_config["user_id"] == "demo_user", "Expected demo user ID"

        print(f"   ✓ Demo mode: {demo_config['connection']}")

    finally:
        # Clean up
        os.unlink(temp_path)


def test_api_wrappers():
    """Test simple API wrapper functions."""
    print("Testing API wrappers...")

    # Create test config
    test_config = {
        "url": "https://api.example.com",
        "connection": "Demo",
        "test_key": "test_value",
    }
    config_str = json.dumps(test_config)

    # Test get_config
    config = core.get_config()
    print(f"   ✓ get_config returned {len(config)} keys")

    # Test get_config_value with JSON string
    os.environ["JGT_CONFIG_JSON_SECRET"] = config_str
    value = core.get_config_value("test_key", "default")
    # Clean up environment
    del os.environ["JGT_CONFIG_JSON_SECRET"]

    print(f"   ✓ get_config_value: {value}")

    # Test is_demo_mode
    demo_mode = core.is_demo_mode()
    print(f"   ✓ is_demo_mode: {demo_mode}")


def main():
    """Run all tests."""
    print("=== jgtcore Test Suite ===\n")

    try:
        test_str_to_datetime()
        print()

        test_market_open()
        print()

        test_datetime_helpers()
        print()

        test_settings_with_temp_file()
        print()

        test_config_loading()
        print()

        test_api_wrappers()

        print("\n=== All tests passed! ===")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        core.print_exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
