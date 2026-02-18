# gputop Development Session History (as of 2026-02-18)

This document summarizes the current state of the `gputop` project, the issues encountered during development, and the next steps.

## Project Status (V0.2/V0.3 Development)

**Project Name:** `gputop` (renamed from `amdtop`)
**Goal:** A GPU monitoring tool, similar to `vtop`, with terminal-based historical graphs and dynamic resizing.

**Key Files in `gputop/` directory:**
*   `gputop_v0.2.py`: **Archived** Version 0.2 Python application code. This file should remain **untouched**. It implements dynamic resizing, flicker reduction, colorized/aligned text output, and the `-i <n>` option with "refresh in place" behavior.
*   `gputop.py`: **Active** Version 0.3 Python application code. This file was created as a copy of `gputop_v0.2.py` and is where V0.3 development should continue. It includes the shebang `#!/usr/bin/env python3`.
*   `gputop`: **Wrapper/Launcher Script**. This is an executable Bash script (`#!/bin/bash`) designed to run `gputop.py` using its virtual environment's Python interpreter.

**Key Features Implemented so far (V0.2 complete, V0.3 in progress):**
*   Dynamic discovery of AMD GPU and `hwmon` paths.
*   Display of GPU Utilization, Memory Utilization, VRAM usage, Temperatures (Edge, Junction, Memory), Clocks (sclk, mclk), Power, and Fan speed.
*   Historical graphs (histograms) for GPU Utilization, Memory Utilization, and Junction Temperature.
*   Dynamic resizing of histograms and display elements based on terminal window size.
*   Significant reduction in display flicker.
*   Colorized and aligned text output for better readability.
*   Command-line option `-i <n>` for finite iterations with "refresh in place" behavior (clears screen, prints new output).
*   Program made directly executable via a wrapper script (`./gputop`).

## Recent Issues and Debugging

The primary recurring issue is `ModuleNotFoundError: No module named 'blessed'` when attempting to run `gputop` directly (e.g., `./gputop`).

**Analysis of the problem:**
*   `blessed` *is* confirmed to be installed in the virtual environment (`gputop/venv/lib/python3.12/site-packages/`).
*   The `gputop` wrapper script has executable permissions and correctly points to `gputop.py`. Its shebang `#!/bin/bash` is correct.
*   The error suggests that the system is trying to execute `/home/timo/gputop/gputop` (the *wrapper script*) directly as a Python script, not as a Bash script. This would happen if the shebang `#!/bin/bash` is being ignored, or if the shell is not interpreting `gputop` as a shell script.

This is a fundamental execution environment issue that prevents the wrapper script from correctly invoking the virtual environment's Python.

## Current Task

We were in the middle of implementing the user's request for V0.3:
*   Add version number ("V0.3") and "by OH8XAT" to the header text within `gputop/gputop.py`. (This change has been made to `gputop/gputop.py` but not yet committed).
*   After this, the user asked questions about installation and deployment paths for new users.

## Next Steps

The immediate priority for V0.3 development is to **resolve the `ModuleNotFoundError` and ensure the `gputop` wrapper script executes correctly and reliably**.

Further debugging is needed to understand why the `#!/bin/bash` shebang in the wrapper script is being ignored, or why the shell is attempting to run it as a Python script directly. This might involve looking at the user's shell configuration or environment.

**Suggested next actions:**
1.  **Commit the current changes** in `gputop.py` (adding V0.3 and author to header).
2.  **Further diagnose the execution issue:**
    *   Ask the user for their `$SHELL` and `echo $PATH`.
    *   Test the wrapper script in isolation by adding `set -x` to the top of `gputop` to trace its execution.
    *   Attempt to manually execute the `exec "$VENV_PYTHON" "$APP_SCRIPT" "$@"` line from within the `gputop` directory in an activated virtual environment to see if it works.

This detailed history should help us resume effectively.
