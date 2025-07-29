#!/usr/bin/env python3

"""
Example usage of jgtcore library

This demonstrates how to use the extracted core functions
from jgtutils without CLI dependencies.
"""

import os
import sys

# Add the current directory to Python path so we can import jgtcore
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core as jgtcore


def main():
    """Example usage of jgtcore functions."""

    print("=== jgtcore Example Usage ===\n")

    # 1. Simple setup for external packages
    print("1. Setting up environment...")
    try:
        config, settings = jgtcore.setup_environment(demo=True)
        print(f"   ✓ Config loaded with {len(config)} keys")
        print(f"   ✓ Settings loaded with {len(settings)} keys")
    except Exception as e:
        print(f"   ✗ Setup failed: {e}")

    # 2. Get specific configuration values
    print("\n2. Getting configuration values...")
    try:
        url = jgtcore.get_config_value("url", "default-url")
        print(f"   URL: {url}")

        demo_mode = jgtcore.is_demo_mode()
        print(f"   Demo mode: {demo_mode}")
    except Exception as e:
        print(f"   ✗ Config access failed: {e}")

    # 3. Get specific settings
    print("\n3. Getting settings...")
    try:
        timeframe = jgtcore.get_setting("timeframe", "H1")
        instrument = jgtcore.get_setting("instrument", "EUR/USD")
        print(f"   Default timeframe: {timeframe}")
        print(f"   Default instrument: {instrument}")
    except Exception as e:
        print(f"   ✗ Settings access failed: {e}")

    # 4. Utility functions
    print("\n4. Utility functions...")

    # Date/time utilities
    last_week = jgtcore.dt_from_last_week_as_string_fxformat()
    print(f"   Last week (FX format): {last_week}")

    # Market status
    market_open = jgtcore.is_market_open()
    print(f"   Market open: {market_open}")

    # String to datetime conversion
    test_date = "2024-01-15 10:30:00"
    parsed_date = jgtcore.str_to_datetime(test_date)
    print(f"   Parsed date '{test_date}': {parsed_date}")

    # 5. Trading connection parameters
    print("\n5. Trading connection...")
    try:
        user_id, password, url, connection, account = jgtcore.read_fx_str_from_config(
            demo=True
        )
        print(f"   Connection: {connection}")
        print(f"   URL: {url}")
        print(f"   Account: {account}")
        print(f"   User ID: {user_id[:3]}... (hidden)")
    except Exception as e:
        print(f"   ✗ Trading config failed: {e}")

    print("\n=== Example completed ===")


if __name__ == "__main__":
    main()
