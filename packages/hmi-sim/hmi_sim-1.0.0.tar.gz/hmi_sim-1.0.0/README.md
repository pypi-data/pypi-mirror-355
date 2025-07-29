# HMI-Sim

**A Python utility for simulating human-like mouse movement and task switching — useful for automation, UI testing, and system interaction simulations.**


## Overview

**HMI-Sim** (Human-Machine Interaction Simulator) is a lightweight Python script designed to programmatically simulate human input patterns, including dynamic mouse movements and application switching via keyboard shortcuts.

It provides an easy way to mimic basic input activity for development, testing, or automation workflows where synthetic interaction is required — such as simulating user behavior for demos, system monitoring tools, or GUI test environments.


## Features

- 🖱️ Mouse cursor movement with configurable speed and motion paths
- ⌨️ Programmatic taskbar app switching using `Win + [Number]`
- 🔁 Periodic activity simulation with randomized timing
- 🔊 Optional voice-based feedback (Windows only)
- ⚙️ Simple configuration via `config.ini` file with randomized ranges for natural variability
- 🧪 CLI support with optional simulation duration


## Use Cases

- UI interaction testing
- Automation workflows
- Development of interaction-based tools
- Demos requiring simulated user activity
- Triggering activity-aware system tools

> **Note:** HMI-Sim is intended for use in testing, automation, and simulation workflows. It is not intended for deceptive use.


## Installation

Install via pip:

```bash
pip install hmi-sim
```

Or clone the repository and run directly:

```bash
git clone https://github.com/rohitlal125555/hmi-sim.git
cd hmi_sim
python cli.py
```

## Usage

You can run the simulator directly from the command line:

```bash
hmi-sim --duration <time>
```

### Duration Format
You can control how long the simulation runs using the --duration argument. Supported formats:

- `s` for seconds (e.g., `30s`, `90s`)
- `m` for minutes (e.g., `5m`, `10m`)
- `h` for hours (e.g., `1h`, `2h`)

> If you omit the `--duration` flag, the simulation runs indefinitely until manually stopped.

To stop: press `Ctrl + C`.

## Configuration

All simulation configuration settings are defined in the `config.ini` file, which is automatically created on first run.

### 📂 Config file path:

```bash
``~/.hmi-sim/config.ini
```

- On Windows, this resolves to: `%USERPROFILE%\.hmi-sim\config.ini`
- On Linux/macOS, this resolves to: `$HOME/.hmi-sim/config.ini`

### Sample config.ini:

```ini
[Settings]
; If enabled, the program speaks the app # and num mouse movements chosen for the sim
enable_audio = False

; Enable random clicks
enable_random_clicks = False

; Sleep time between each simulation
sleep_time_range = 30, 60

; Range of apps on task bar to switch between. For eg: 1 - means 1st icon on taskbar
taskbar_apps_range = 2, 6

; Number of intra-simulation mouse movements
num_mouse_movements = 1, 4

; Speed of mouse movement. For eg: 2 - means the mouse movement will take 2s to complete
mouse_movement_speed = 1, 3

```

You can adjust these ranges to suit your testing or simulation scenarios.


## Requirements

- Python 3.9+
- Required Libraries:
  - `pyautogui`
  - `pywin32` (only if `enable_audio = True`)

Install dependencies manually (if cloned):

```bash
pip install pyautogui pywin32
```


## Disclaimer

This tool is provided **for automation and testing purposes only**.

The author assumes no responsibility for any unintended use of this utility. Users are expected to comply with
all applicable laws, policies, and ethical standards.


## License

Licensed under the [Apache License 2.0](https://github.com/rohitlal125555/HMI-Sim/blob/main/LICENSE).


## Contributing

Contributions, suggestions, and improvements are welcome! Please open an 
[issue](https://github.com/rohitlal125555/hmi-sim/issues) or submit a 
[pull request](https://github.com/rohitlal125555/hmi-sim/pulls).
