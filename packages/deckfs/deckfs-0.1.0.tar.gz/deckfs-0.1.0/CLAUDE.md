# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

deckfs - a Linux daemon that provides Stream Deck control without GUI through filesystem interface. Uses modular event-driven architecture with comprehensive error handling and production-ready features.

## Key Features

- **Filesystem-based configuration** with hot-reloading
- **Three script types**: action (on press), update (on startup), background (continuous)
- **Debounced event system** to prevent cascading reloads
- **Crash protection** for background scripts with restart limits
- **Thread-safe operations** with proper cleanup

## Configuration Structure

```
~/.local/streamdeck/
├── config.yaml (optional - daemon settings)
├── env.local (optional - environment variables)
├── 01/
│   ├── image.png (button image, PNG/JPEG, can be symlink)
│   ├── action.{sh,py,js} (optional - executed on button press)
│   ├── update.{sh,py,js} (optional - sync state on startup)
│   └── background.{sh,py,js} (optional - continuous monitoring)
├── 02/
│   ├── image.jpg
│   └── action.py
└── ...
```

### Script Types

- **action.{sh,py,js}**: Fire-and-forget execution on button press
- **update.{sh,py,js}**: Synchronous execution on daemon start/restart (30s timeout)
- **background.{sh,py,js}**: Continuous execution with crash protection and auto-restart


## Architecture

**Core Components**:
- `src/core/daemon.py` - Simple daemon entry point, delegates to Coordinator
- `src/core/coordinator.py` - **Coordinator** - high-level orchestrator handling button management, file watching, and coordination
- `src/core/hardware.py` - **DeviceHardwareManager** - hardware abstraction layer for device connection, USB monitoring, and key events
- `src/core/button.py` - **Button** class - individual button logic with process lifecycle management
- `src/core/files.py` - **FileWatcher** - watchdog-based filesystem monitoring with debouncing
- `src/core/processes.py` - **ProcessManager** - script execution with crash protection and lifecycle management

**Utilities**:
- `src/utils/config.py` - YAML configuration loading with environment variable support
- `src/utils/debouncer.py` - **EventBus** - centralized event system with debouncing
- `src/utils/file_utils.py` - File operation helpers
- `src/utils/logger.py` - Logging with different levels
- `src/utils/image_utils.py` - Image loading and preparation for StreamDeck

## Key Implementation Details

**Event Flow**:
1. `FileWatcher` detects filesystem changes via watchdog
2. Events are debounced through `EventBus` to prevent cascading
3. `StreamDeckManager` processes debounced events
4. Only affected buttons are reloaded (not all buttons)
5. `Button` instances manage their own process lifecycles

**Process Management**:
- Background scripts have crash protection (5 crashes per 5-minute window)
- Update scripts run synchronously with 30-second timeout
- Action scripts are fire-and-forget with no timeout
- All scripts auto-detect interpreter (.sh→bash, .py→python3, .js→node)

**Thread Safety**:
- All operations are thread-safe with proper locking
- Graceful shutdown with resource cleanup
- Background script termination on daemon exit

## Testing

Uses pytest with comprehensive mocking:
- `tests/test_debouncer.py` - Event bus and debouncing logic
- `tests/test_button.py` - Button lifecycle and process management
- `tests/test_process_manager.py` - Script execution and crash protection  
- `tests/test_file_operations.py` - File watching and event handling

## Examples

Available in `examples/` directory:
- `01_toggle_mute/` - Bash scripts with background monitoring (mute state tracking)
- `02_launch_firefox/` - Simple Python action script
- `03_next_track/` - JavaScript action script with D-Bus integration
- `04_clock/` - Python background script for dynamic clock display

# Important Instructions

## Language Policy
**CRITICAL**: This is an English-only codebase. ALL code, comments, strings, documentation, and .md files must be in English to maintain international accessibility. User instructions may be in Russian, but all code output, comments, and documentation must be in English.

## General Guidelines
Follow YAGNI/DRY/KISS principles. Maintain simplicity and readability.
When writing comments, use them to tell WHY the code is the way it is, not WHAT it does.
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
