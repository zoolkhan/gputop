import os
import time
import glob
import argparse
from blessed import Terminal

# HISTORY_LENGTH will be dynamic based on terminal width
# graph_height will be dynamic based on terminal height

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

def draw_history_graph(term, history, max_value, height, start_y, start_x, color):
    """Draws a historical line graph using block characters."""
    output = ""
    # Ensure graph is cleared for the given area
    for y_clear in range(height):
        output += term.move_xy(start_x, start_y + y_clear) + ' ' * len(history)

    for x, value in enumerate(history):
        scaled_value = int((value / max_value) * height)
        if scaled_value > height: scaled_value = height
        if value > 0 and scaled_value == 0: scaled_value = 1

        for y_draw in range(scaled_value):
            output += term.move_xy(start_x + x, start_y + height - 1 - y_draw) + color + '█' + term.normal
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

def display_metrics(term, metrics, iteration_type="continuous", history_data=None, current_line_start=0, HISTORY_LENGTH=0):
    """Displays the collected metrics."""
    gpu_util, mem_util, used_vram, total_vram, edge_temp, junction_temp, mem_temp, sclk, mclk, power, fan = metrics
    frame_output = ""
    
    # Max length of labels for alignment
    LABEL_PAD = max(len("GPU Utilization"), len("Memory Utilization"), 
                    len("VRAM"), len("Temperatures"), len("Clocks"), len("Power")) + 2 # +2 for ": "

    if iteration_type == "continuous":
        frame_output += term.move_xy(0, 0) + term.center(term.bold_white + "GPU Monitor" + term.normal)
        frame_output += term.move_xy(0, 1) + term.center(term.bold_white + "===============" + term.normal)
        current_line = 4
    else: # single/finite iterations
        # In non-continuous mode, we don't use blessed's move_xy for text output
        # so we just build plain strings and print them.
        # Clearing is handled by os.system('clear') before calling this function.
        frame_output += term.bold_white + "GPU Monitor" + term.normal + "\n"
        frame_output += term.bold_white + "===============" + term.normal + "\n\n"
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
        gpu_util_history, mem_util_history, temp_junction_history = history_data
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
        frame_output += draw_history_graph(term, gpu_util_history, 100, graph_height, current_line, graph_start_x, term.on_green)
        current_line += graph_height + 1

        # Memory Utilization Graph
        frame_output += term.move_xy(0, current_line) + term.clear_eol + term.blue + "Memory Utilization History:" + term.normal
        current_line += 1
        frame_output += draw_history_graph(term, mem_util_history, 100, graph_height, current_line, graph_start_x, term.on_blue)
        current_line += graph_height + 1

        # Junction Temperature Graph
        frame_output += term.move_xy(0, current_line) + term.clear_eol + term.red + "Junction Temperature History:" + term.normal
        current_line += 1
        frame_output += draw_history_graph(term, temp_junction_history, 120, graph_height, current_line, graph_start_x, term.on_red)
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
    HISTORY_LENGTH = term.width - 4 if args.iterations == 0 else 0 # No history if not continuous
    gpu_util_history = [0] * HISTORY_LENGTH
    mem_util_history = [0] * HISTORY_LENGTH
    temp_junction_history = [0] * HISTORY_LENGTH
    
    iteration_count = 0
    
    if args.iterations == 0: # Continuous mode with fullscreen
        with term.fullscreen(), term.cbreak(), term.hidden_cursor():
            try:
                while True:
                    with term.location(0, 0):
                        try:
                            metrics = collect_metrics(card_device_dir, hwmon_dir)
                            gpu_util, mem_util, _, _, edge_temp, junction_temp, _, _, _, _, _ = metrics

                            gpu_util_history.append(gpu_util)
                            gpu_util_history = gpu_util_history[-HISTORY_LENGTH:]
                            mem_util_history.append(mem_util)
                            mem_util_history = mem_util_history[-HISTORY_LENGTH:]
                            temp_junction_history.append(int(junction_temp))
                            temp_junction_history = temp_junction_history[-HISTORY_LENGTH:]

                            frame_output = display_metrics(term, metrics, "continuous", 
                                                           (gpu_util_history, mem_util_history, temp_junction_history))
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
