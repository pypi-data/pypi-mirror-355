# pybtm

A cross-platform interactive process monitor for Linux and macOS, inspired by `top`, built with [psutil](https://github.com/giampaolo/psutil) and [rich](https://github.com/Textualize/rich).

## Features
- Interactive process table with live updates
- Navigate with J/K or Up/Down arrows
- Kill selected process with X
- Shows PID, name, CPU %, and RAM usage (MB)
- Adjustable snapshot frequency (default: 3 seconds)
- Works on Linux and macOS

## Installation
```bash
pip install .
```

## Usage
```bash
pybtm [-f FREQUENCY]
```
- `-f`, `--frequency`: Set snapshot frequency in seconds (default: 3)

## Controls
- `j` / Down Arrow: Move selection down
- `k` / Up Arrow: Move selection up
- `x`: Kill selected process (SIGKILL)
- `q`: Quit
- Space Bar: Freeze process sequence

## Requirements
- Python 3.8+
- psutil
- rich

## Notes
- Killing processes may require root/administrator privileges.
- Some processes may not show all information due to system permissions. 
