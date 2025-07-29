# jgtcore

Core library for JGT utilities - configuration, settings, and utility functions.

This is a pure Python library extracted from `jgtutils` to provide clean programmatic access to JGT configuration and settings without CLI dependencies.

## Installation

```bash
pip install jgtcore
```

## Usage

### Simple Configuration Access
```python
import jgtcore

# Load configuration
config = jgtcore.get_config()
demo_config = jgtcore.get_config(demo=True)

# Get specific config values
user_id = jgtcore.get_config_value('user_id')
quotes_count = jgtcore.get_config_value('quotes_count', 1000)
```

### Settings Management
```python
import jgtcore

# Get all settings
settings = jgtcore.get_settings()

# Get specific setting with default
instrument = jgtcore.get_setting('instrument', 'EUR/USD')
timeframes = jgtcore.get_setting('_timeframes', 'D1')
```

### Environment Setup
```python
import jgtcore

# One-call environment setup
config, settings = jgtcore.setup_environment(demo=True)

# Check demo mode
if jgtcore.is_demo_mode():
    print("Running in demo mode")
```

### Advanced Usage
```python
from jgtcore import readconfig, load_settings

# Load with specific options
config = readconfig(demo=True, export_env=True)
settings = load_settings(custom_path="/path/to/settings.json")
```

## Configuration Files

- **config.json**: Trading credentials and connection settings
- **settings.json**: Application settings and preferences

See `examples/` directory for sample configuration files.

## File Locations

### config.json lookup order:
1. Current directory: `config.json`
2. User home: `~/.jgt/config.json`
3. System: `/etc/jgt/config.json`
4. Environment variables: `JGT_CONFIG`, `JGT_CONFIG_PATH`

### settings.json lookup order:
1. System: `/etc/jgt/settings.json`
2. User home: `~/.jgt/settings.json`
3. Current directory: `.jgt/settings.json`
4. YAML variants: `jgt.yml`, `_config.yml`
5. Environment variables: `JGT_SETTINGS`

## License

MIT License