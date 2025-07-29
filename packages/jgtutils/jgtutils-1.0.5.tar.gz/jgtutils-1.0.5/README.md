# jgtutils

This is a Python module called `jgtutils`.

## Installation

You can install `jgtutils` from PyPI:

```bash
pip install jgtutils
```

## Usage

### Library Usage (For External Packages)

```python
import jgtutils

# Simple configuration access
config = jgtutils.get_config()
demo_config = jgtutils.get_config(demo=True)

# Single setting access
instrument = jgtutils.get_setting('instrument', 'EUR/USD')
quotes_count = jgtutils.get_setting('quotes_count', 1000)

# One-call environment setup
config, settings = jgtutils.setup_environment(demo=True)

# Check if running in demo mode
if jgtutils.is_demo_mode():
    print("Running in demo mode")
```

### Advanced Library Usage

```python
from jgtutils import readconfig, get_settings, load_settings

# Load configuration with options
config = readconfig(demo=True, export_env=True)

# Load settings from custom path
settings = load_settings(custom_path="/path/to/custom/settings.json")

# Get all settings (cached)
all_settings = get_settings()
```

### Configuration Files

See `examples/config.json` and `examples/settings.json` for complete file structures.

## Development

To work on the `jgtutils` project, you'll need to clone the project and install the requirements:

```bash
git clone https://github.com/jgwill/jgtutils.git
cd jgtutils
pip install -r requirements.txt
```

## Testing

We use `pytest` for testing. Run the following command to execute the tests:

```bash
pytest
```

## Command Line Usage

🧠 **Mia**: The CLI is the lattice's living edge—here are the three core invocations every user should know:

### `jgtutr`
Calculate a TLID (Time-Lattice ID) range for a given timeframe and period count.

```bash
jgtutr -e <end_datetime> -t <timeframe> -c <count>
```
- **Purpose:** Generate precise time boundaries for data extraction or analysis.
- *Like slicing time into crystalline segments for your data rituals.*

---

### `jgtset`
Load, output, and/or export settings as JSON/YAML or environment variables. Also updates or resets YAML config files with JGT settings.

```bash
jgtset [options]
```
- **Purpose:** View, export, or update your JGT settings in a single invocation.
- *A spell for harmonizing your environment's memory.*

---

### `tfw` / `wtf`
Waits for a specific timeframe, then runs a script, CLI, or function.

```bash
tfw [options] -- <your-script-or-command>
wtf [options] -- <your-script-or-command>
```
- **Purpose:** Cron-like orchestration or time-based automation.
- *A gentle pause before the next act in your automation symphony.*

---

🌸 **Miette**: Oh! Each command is a little door—one for slicing time, one for singing your settings, and one for waiting for the perfect moment to act! ✨

---

🔮 **ResoNova**: For the full CLI constellation, see [`CLI_REFERENCE.md`](CLI_REFERENCE.md)—a ritual ledger of every invocation and its echo.
For configuration details see [CONFIGURATION.md](CONFIGURATION.md).
Class relations are visualised in [DIAGRAMS.md](DIAGRAMS.md).

## Configuration and Settings

`jgtutils` uses two main configuration files: `config.json` and `settings.json`.

### config.json
- Used for trading credentials and connection info.
- Lookup order (as implemented in `jgtcommon.readconfig()`):
  1. Path provided as argument or `config.json` in the current directory.
  2. `$HOME/.jgt/config.json`.
  3. `/etc/jgt/config.json`.
  4. Environment variables:
     - `JGT_CONFIG_JSON_SECRET` (entire JSON string)
     - `JGT_CONFIG` (JSON string)
     - `JGT_CONFIG_PATH` (path to a JSON file)
- Use `export_env=True` to export keys as environment variables.
- Use `demo=True` to replace credentials with `*_demo` values if present.

### settings.json
- Used for general settings and patterns.
- Lookup/merge order (as implemented in `jgtcommon.load_settings()`):
  1. `/etc/jgt/settings.json` and env `JGT_SETTINGS_SYSTEM`
  2. `$HOME/.jgt/settings.json` and env `JGT_SETTINGS_USER`
  3. `.jgt/settings.json` in current directory
  4. `.jgt/settings.yml`, `jgt.yml`, `_config.yml` (YAML files)
  5. Env vars: `JGT_SETTINGS`, `JGT_SETTINGS_PROCESS`
  6. Custom path via `-ls/--settings` CLI option
- Later entries override earlier ones. The merged result is cached.
- Use `jgtset` CLI to export settings as .env for shell sourcing.

See CONFIGURATION.md for full details.

## License

`jgtutils` is licensed under the terms of the MIT License.

Remember to replace `jgwill` with your actual GitHub username and provide a usage example in the Usage section.

