#!/usr/bin/env python3
import os
import time
import glob
import argparse
from blessed import Terminal

# HISTORY_LENGTH will be dynamic based on terminal width
# graph_height will be dynamic based on terminal height

def get_gpu_model():
    """Gets the GPU model name using lspci."""
    try:
        import subprocess
        output = subprocess.check_output("lspci -d 1002:", shell=True).decode()
        for line in output.splitlines():
            if "VGA compatible controller" in line or "Display controller" in line:
                # Extract the part after the colon
                model = line.split(":", 2)[-1].strip()
                # Remove [AMD/ATI] prefix if present
                model = model.replace("[AMD/ATI]", "").strip()
                return model
    except Exception:
        pass
    return "AMD GPU"

def find_amd_gpu_card():
    """Finds the AMD GPU card directory."""
    for card in glob.glob("/sys/class/drm/card*"):
        try:
            with open(os.path.join(card, "device", "uevent"), "r") as f:
                if "amdgpu" in f.read():
                    return os.path.join(card, "device")
        except FileNotFoundError:
            continue
    return None

def find_hwmon_dir(card_device_dir):
    """Finds the hwmon directory for a given card."""
    hwmon_dirs = glob.glob(os.path.join(card_device_dir, "hwmon", "hwmon*"))
    if hwmon_dirs:
        return hwmon_dirs[0]
    return None

def get_gpu_utilization(card_device_dir):
    """Gets the GPU utilization."""
    with open(os.path.join(card_device_dir, "gpu_busy_percent"), "r") as f:
        return int(f.read().strip())

def get_mem_utilization(card_device_dir):
    """Gets the memory controller utilization."""
    with open(os.path.join(card_device_dir, "mem_busy_percent"), "r") as f:
        return int(f.read().strip())

def get_vram_info(card_device_dir):
    """Gets the VRAM information."""
    with open(os.path.join(card_device_dir, "mem_info_vram_used"), "r") as f:
        used_vram = int(f.read().strip())
    with open(os.path.join(card_device_dir, "mem_info_vram_total"), "r") as f:
        total_vram = int(f.read().strip())
    return used_vram, total_vram

def get_temperatures(hwmon_dir):
    """Gets the GPU temperatures."""
    with open(os.path.join(hwmon_dir, "temp1_input"), "r") as f:
        edge = int(f.read().strip()) / 1000
    with open(os.path.join(hwmon_dir, "temp2_input"), "r") as f:
        junction = int(f.read().strip()) / 1000
    with open(os.path.join(hwmon_dir, "temp3_input"), "r") as f:
        mem = int(f.read().strip()) / 1000
    return edge, junction, mem

def get_clocks(hwmon_dir):
    """Gets the GPU clocks."""
    with open(os.path.join(hwmon_dir, "freq1_input"), "r") as f:
        sclk = int(f.read().strip()) // 1000000
    with open(os.path.join(hwmon_dir, "freq2_input"), "r") as f:
        mclk = int(f.read().strip()) // 1000000
    return sclk, mclk

def get_power_and_fan(hwmon_dir):
    """Gets the power and fan information."""
    with open(os.path.join(hwmon_dir, "power1_average"), "r") as f:
        power = int(f.read().strip()) // 1000000
    with open(os.path.join(hwmon_dir, "fan1_input"), "r") as f:
        fan = int(f.read().strip())
    return power, fan

def get_color(term, value, max_value):
    """Returns a color based on the value's percentage of max_value."""
    percentage = (value / max_value) * 100
    if percentage < 50:
        return term.green
    elif percentage < 70:
        return term.yellow
    elif percentage < 90:
        return term.orange if hasattr(term, 'orange') else term.color(208) # ANSI 208 is orange
    else:
        return term.red

def draw_history_graph(term, history, max_value, height, start_y, start_x, history_type="percent", total_vram=0, min_value=0):
    """Draws a historical line graph using braille characters with color gradients."""
    output = ""
    # BRAILLE_BARS: 0, 1, 2, 3, 4 rows filled (bottom to top)
    BRAILLE_BARS = [' ', '⣀', '⣤', '⣶', '⣿']
    
    # Draw Y-axis labels
    label_count = 5
    range_val = max_value - min_value
    for i in range(label_count):
        label_val = min_value + int((range_val / (label_count - 1)) * i)
        if history_type == "memory":
            if label_val >= 1024**3:
                label_str = f"{label_val // 1024**3}G"
            elif label_val >= 1024**2:
                label_str = f"{label_val // 1024**2}M"
            else:
                label_str = f"{label_val // 1024}K"
        elif history_type == "temp":
            label_str = f"{label_val}°C"
        else:
            label_str = f"{label_val}%"
        
        y_pos = start_y + height - 1 - int((i / (label_count - 1)) * (height - 1))
        # f"{label_str:>5}┤" ensures consistent alignment if label_str is up to 5 chars (e.g. 120°C)
        output += term.move_xy(0, y_pos) + term.white + f"{label_str:>5}┤" + term.normal

    # Ensure graph is cleared for the given area
    graph_start_x = start_x + 6 # Offset for Y-axis labels
    for y_clear in range(height):
        output += term.move_xy(graph_start_x, start_y + y_clear) + ' ' * len(history)

    for x, value in enumerate(history):
        color = get_color(term, value, max_value)
        # Total vertical dots available: height * 4
        total_dots = height * 4
        
        # Scale value relative to [min_value, max_value]
        val_rel = max(0, value - min_value)
        scaled_dots = int((val_rel / range_val) * total_dots) if range_val > 0 else 0
        
        if scaled_dots > total_dots: scaled_dots = total_dots
        if val_rel > 0 and scaled_dots == 0: scaled_dots = 1

        full_chars = scaled_dots // 4
        partial_dots = scaled_dots % 4
        
        # Draw full characters from bottom up
        for y_full in range(full_chars):
            output += term.move_xy(graph_start_x + x, start_y + height - 1 - y_full) + color + '⣿' + term.normal
        
        # Draw partial character if needed
        if partial_dots > 0 and full_chars < height:
            output += term.move_xy(graph_start_x + x, start_y + height - 1 - full_chars) + color + BRAILLE_BARS[partial_dots] + term.normal
            
    return output

def collect_metrics(card_device_dir, hwmon_dir):
    """Collects all GPU metrics."""
    gpu_util = get_gpu_utilization(card_device_dir)
    mem_util = get_mem_utilization(card_device_dir)
    used_vram, total_vram = get_vram_info(card_device_dir)
    edge_temp, junction_temp, mem_temp = get_temperatures(hwmon_dir)
    sclk, mclk = get_clocks(hwmon_dir)
    power, fan = get_power_and_fan(hwmon_dir)
    return gpu_util, mem_util, used_vram, total_vram, edge_temp, junction_temp, mem_temp, sclk, mclk, power, fan

def display_metrics(term, metrics, iteration_type="continuous", history_data=None, current_line_start=0, HISTORY_LENGTH=0, gpu_name="AMD GPU"):
    """Displays the collected metrics."""
    gpu_util, mem_util, used_vram, total_vram, edge_temp, junction_temp, mem_temp, sclk, mclk, power, fan = metrics
    frame_output = ""
    
    # Max length of labels for alignment
    LABEL_PAD = max(len("GPU Utilization"), len("Memory Utilization"), 
                    len("VRAM"), len("Temperatures"), len("Clocks"), len("Power")) + 2 # +2 for ": "

    if iteration_type == "continuous":
        frame_output += term.move_xy(0, 0) + term.center(term.blue + "gputop V1.0 by OH8XAT" + term.normal)
        frame_output += term.move_xy(0, 1) + term.center(term.cyan + gpu_name + term.normal)
        current_line = 3
    else: # single/finite iterations
        # In non-continuous mode, we don't use blessed's move_xy for text output
        # so we just build plain strings and print them.
        # Clearing is handled by os.system('clear') before calling this function.
        frame_output += term.blue + "gputop V1.0 by OH8XAT" + term.normal + "\n"
        frame_output += term.cyan + gpu_name + term.normal + "\n\n"
        current_line = current_line_start # Use the passed start line

    frame_output += (term.move_xy(0, current_line) if iteration_type == "continuous" else "") + \
                    f"{term.green}{'GPU Utilization':<{LABEL_PAD}}{term.normal}: {gpu_util}%\n"
    current_line += 1 if iteration_type == "continuous" else 1
    frame_output += (term.move_xy(0, current_line) if iteration_type == "continuous" else "") + \
                    f"{term.blue}{'Memory Utilization':<{LABEL_PAD}}{term.normal}: {mem_util}%\n"
    current_line += 1 if iteration_type == "continuous" else 1
    frame_output += (term.move_xy(0, current_line) if iteration_type == "continuous" else "") + \
                    f"{term.cyan}{'VRAM':<{LABEL_PAD}}{term.normal}: {used_vram // 1024 // 1024}MB / {total_vram // 1024 // 1024}MB\n"
    current_line += 1 if iteration_type == "continuous" else 1
    frame_output += (term.move_xy(0, current_line) if iteration_type == "continuous" else "") + \
                    f"{term.red}{'Temperatures':<{LABEL_PAD}}{term.normal}: Edge={edge_temp}°C, Junction={junction_temp}°C, Memory={mem_temp}°C\n"
    current_line += 1 if iteration_type == "continuous" else 1
    frame_output += (term.move_xy(0, current_line) if iteration_type == "continuous" else "") + \
                    f"{term.magenta}{'Clocks':<{LABEL_PAD}}{term.normal}: sclk={sclk}MHz, mclk={mclk}MHz\n"
    current_line += 1 if iteration_type == "continuous" else 1
    frame_output += (term.move_xy(0, current_line) if iteration_type == "continuous" else "") + \
                    f"{term.yellow}{'Power':<{LABEL_PAD}}{term.normal}: {power}W, Fan: {fan}RPM\n"
    current_line += 2 if iteration_type == "continuous" else 1 # Add a blank line for spacing

    if iteration_type == "continuous": # Only draw histograms if in continuous mode
        gpu_util_history, vram_history, temp_junction_history = history_data
        # Calculate available height for graphs
        stats_lines = current_line # Lines used by header and text stats
        lines_per_graph_label = 1 # Each graph label takes 1 line
        total_graph_labels_lines = 3 * lines_per_graph_label
        
        available_height_for_graphs = term.height - stats_lines - total_graph_labels_lines - 1 # -1 for bottom margin
        graph_height = max(3, available_height_for_graphs // 3) # Min height of 3 per graph

        graph_start_x = 2 # Starting X position for graphs, leave margin for labels

        # GPU Utilization Graph
        frame_output += term.move_xy(0, current_line) + term.clear_eol + term.green + "GPU Utilization History:" + term.normal
        current_line += 1
        frame_output += draw_history_graph(term, gpu_util_history, 100, graph_height, current_line, graph_start_x, "percent")
        current_line += graph_height + 1

        # VRAM Usage Graph
        frame_output += term.move_xy(0, current_line) + term.clear_eol + term.blue + "VRAM Usage History:" + term.normal
        current_line += 1
        frame_output += draw_history_graph(term, vram_history, total_vram, graph_height, current_line, graph_start_x, "memory")
        current_line += graph_height + 1

        # Junction Temperature Graph
        frame_output += term.move_xy(0, current_line) + term.clear_eol + term.red + "Junction Temperature History:" + term.normal
        current_line += 1
        frame_output += draw_history_graph(term, temp_junction_history, 120, graph_height, current_line, graph_start_x, "temp", min_value=20)
        current_line += graph_height + 1
    
    return frame_output


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="GPU monitoring tool.")
    parser.add_argument("-i", "--iterations", type=int, default=0,
                        help="Run for N iterations and exit. 0 for continuous.")
    args = parser.parse_args()

    term = Terminal()
    card_device_dir = find_amd_gpu_card()
    if not card_device_dir:
        print("Could not find an AMD GPU.")
        return

    hwmon_dir = find_hwmon_dir(card_device_dir)
    if not hwmon_dir:
        print("Could not find hwmon directory for the AMD GPU.")
        return

    # Initialize histories
    gpu_name = get_gpu_model()
    HISTORY_LENGTH = term.width - 10 if args.iterations == 0 else 0 # Adjust for Y-axis labels
    gpu_util_history = [0] * HISTORY_LENGTH
    vram_history = [0] * HISTORY_LENGTH
    temp_junction_history = [0] * HISTORY_LENGTH
    
    last_width, last_height = term.width, term.height
    iteration_count = 0
    
    if args.iterations == 0: # Continuous mode with fullscreen
        with term.fullscreen(), term.cbreak(), term.hidden_cursor():
            try:
                while True:
                    # Check for resize
                    if term.width != last_width or term.height != last_height:
                        last_width, last_height = term.width, term.height
                        HISTORY_LENGTH = max(10, term.width - 10)
                        # Re-pad or truncate history to match new width
                        def resize_history(h, new_len):
                            if len(h) < new_len:
                                return [0] * (new_len - len(h)) + h
                            return h[-new_len:]
                        gpu_util_history = resize_history(gpu_util_history, HISTORY_LENGTH)
                        vram_history = resize_history(vram_history, HISTORY_LENGTH)
                        temp_junction_history = resize_history(temp_junction_history, HISTORY_LENGTH)
                        print(term.clear)

                    with term.location(0, 0):
                        try:
                            metrics = collect_metrics(card_device_dir, hwmon_dir)
                            gpu_util, mem_util, used_vram, total_vram, edge_temp, junction_temp, _, _, _, _, _ = metrics

                            gpu_util_history.append(gpu_util)
                            gpu_util_history = gpu_util_history[-HISTORY_LENGTH:]
                            vram_history.append(used_vram)
                            vram_history = vram_history[-HISTORY_LENGTH:]
                            temp_junction_history.append(int(junction_temp))
                            temp_junction_history = temp_junction_history[-HISTORY_LENGTH:]

                            frame_output = display_metrics(term, metrics, "continuous", 
                                                           (gpu_util_history, vram_history, temp_junction_history), 
                                                           HISTORY_LENGTH=HISTORY_LENGTH,
                                                           gpu_name=gpu_name)
                            print(frame_output, end='')

                        except FileNotFoundError as e:
                            print(term.move_xy(0,0) + term.clear_eol + f"Error reading file: {e}. Check if the amdgpu driver is loaded and you have the correct permissions.")
                            break
                        except Exception as e:
                            print(term.move_xy(0,0) + term.clear_eol + f"An error occurred: {e}")
                            break
                    
                    iteration_count += 1
                    if args.iterations > 0 and iteration_count >= args.iterations:
                        break
                    
                    time.sleep(1)
            except KeyboardInterrupt:
                pass # Handled by blessed's cbreak and fullscreen context
            finally:
                print(term.normal + "\n") # Ensure cursor and colors are reset
    else: # Finite iterations, print directly to stdout with clearing
        try:
            while iteration_count < args.iterations:
                os.system('clear') # Clear screen for each iteration
                metrics = collect_metrics(card_device_dir, hwmon_dir)
                frame_output = display_metrics(term, metrics, "finite")
                print(frame_output) # Print directly, no blessed clear/move
                
                iteration_count += 1
                if iteration_count < args.iterations: # Don't sleep after last iteration
                    time.sleep(1) # Still wait a second between iterations to simulate "top -n"
        except KeyboardInterrupt:
            pass # Allow Ctrl+C to exit gracefully
        except FileNotFoundError as e:
            print(f"Error reading file: {e}. Check if the amdgpu driver is loaded and you have the correct permissions.")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
