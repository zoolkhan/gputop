# GPU Monitor V1.0 Development Log

## Plan for V1.0 Improvements

1.  **Title and Header:**
    *   Change title color to dark blue (subtle).
    *   Adjust the underline to match the title length or remove it.
2.  **Histogram Enhancements:**
    *   Implement braille-like characters for the histogram (2x4 grid resolution).
    *   Add color gradients (Green -> Yellow -> Orange -> Red) based on the amplitude.
3.  **Scale Indicators:**
    *   Add Y-axis scales on the left side of the graphs.
    *   GPU: Percent (%)
    *   Memory: GB or KB
    *   Temperature: Celsius (°C)
4.  **Version Update:**
    *   Update all version references from V0.3 to V1.0.

## Execution Steps

*   [x] Backup V0.3 (Done: `gputop_v0.3.py`)
*   [x] Implement subtle title and underline.
    *   Title color changed to `term.blue`.
    *   Underline removed for a cleaner look.
*   [x] Implement Braille-based graph drawing.
    *   `draw_history_graph` rewritten to use Braille characters for vertical bars.
    *   Vertical resolution improved to 4 dots per character height.
*   [x] Implement color mapping for histogram.
    *   `get_color` function added to map percentage to Green/Yellow/Orange/Red.
*   [x] Add Y-axis labels.
    *   Labels added for all graphs: % for GPU, G/M/K for VRAM, °C for temperature.
    *   Graph width adjusted to `term.width - 10` to accommodate labels.
*   [x] Final validation and version bump.
    *   All version references updated to V1.0.
    *   Memory usage now tracked instead of controller utilization in the VRAM graph.
*   [x] Standalone Binary Creation.
    *   Binary `gputop_bin` created using PyInstaller for standalone distribution.
    *   Confirmed execution without external dependencies.
*   [x] GitHub Documentation & Release Prep.
    *   `README.md` updated with V1.0 features and binary instructions.
    *   Project documented and ready for release.
