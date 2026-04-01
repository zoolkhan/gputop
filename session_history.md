# gputop Development Session History (as of 2026-04-01)

This document summarizes the project state, issues encountered, and development history.

## Project Status (V1.0 Reached)

**Project Name:** `gputop`
**Goal:** A GPU monitoring tool for AMD GPUs, with terminal-based historical graphs and dynamic resizing.

**Key Files in `gputop/` directory:**
*   `gputop_v0.2.py`: **Archived** Version 0.2 Python application code.
*   `gputop_v0.3.py`: **Archived** Version 0.3 Python application code.
*   `gputop.py`: **Active** Version 1.0 Python application code.
*   `gputop`: **Wrapper/Launcher Script** (Bash).
*   `project_log.md`: Detailed changelog for V1.0 development.

## V1.0 - Design Overhaul (April 2026)

In this session, the tool was upgraded from V0.3 to V1.0 with a focus on visual design and data representation:

*   **Subtle Header**: Changed the title color to dark blue (`term.blue`) and removed the underline for a more modern, less cluttered look.
*   **Braille Histograms**: Replaced the standard block characters (`█`) with high-resolution Braille characters. This provides 4x the vertical resolution (4 dots per character height), resulting in much smoother graphs.
*   **Amplitude-based Coloring**: Implemented dynamic coloring for the histogram bars. The color now changes based on the value's percentage of the maximum:
    *   0-50%: Green
    *   50-70%: Yellow
    *   70-90%: Orange
    *   >90%: Red
*   **Scale Indicators (Y-Axis)**: Added scale labels to the left of each graph:
    *   **GPU Utilization**: 0% to 100%
    *   **VRAM Usage**: Capacity-based labels (e.g., 0G, 2G, 4G, 6G, 8G) using MB/GB units as appropriate.
    *   **Temperature**: 0°C to 120°C.
*   **VRAM Metrics**: Changed the second graph from "Memory Controller Utilization" (percent) to "VRAM Usage History" (capacity in bytes) to provide more useful information about memory pressure.
*   **Layout Adjustments**: Shifted graphs to the right to accommodate Y-axis labels and adjusted history length calculations to fit the new layout.

## Previous Issues Resolved
*   **Version 0.3**: Added version number and author to header.
*   **Version 0.2**: Implemented dynamic resizing and flicker reduction.

## Future Considerations
*   Support for multiple GPUs.
*   More granular configuration via `settings.json`.
*   Toggle for different graph types (line vs filled).

V1.0 is considered the first stable feature-complete release of the new design.
