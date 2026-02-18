import os
import time
import glob
from blessed import Terminal

HISTORY_LENGTH = 80 # Number of data points to keep for history graphs

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
    for x, value in enumerate(history):
        # Scale value to graph height
        scaled_value = int((value / max_value) * height)
        if scaled_value > height: scaled_value = height
        # Ensure at least one block is drawn if value is > 0
        if value > 0 and scaled_value == 0:
            scaled_value = 1

        # Clear the column first
        for y_clear in range(height):
            output += term.move_xy(start_x + x, start_y + y_clear) + ' '

        # Draw the bar from bottom up
        for y_draw in range(scaled_value):
            output += term.move_xy(start_x + x, start_y + height - 1 - y_draw) + color + '█' + term.normal
    return output

def main():
    """Main function."""
    term = Terminal()
    card_device_dir = find_amd_gpu_card()
    if not card_device_dir:
        print("Could not find an AMD GPU.")
        return

    hwmon_dir = find_hwmon_dir(card_device_dir)
    if not hwmon_dir:
        print("Could not find hwmon directory for the AMD GPU.")
        return

    gpu_util_history = [0] * HISTORY_LENGTH
    mem_util_history = [0] * HISTORY_LENGTH
    temp_junction_history = [0] * HISTORY_LENGTH

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        try:
            while True:
                with term.location(0, 0):
                    print(term.clear)
                    print(term.center("AMD GPU Monitor"))
                    print(term.center("==============="))

                    try:
                        gpu_util = get_gpu_utilization(card_device_dir)
                        mem_util = get_mem_utilization(card_device_dir)
                        used_vram, total_vram = get_vram_info(card_device_dir)
                        edge_temp, junction_temp, mem_temp = get_temperatures(hwmon_dir)
                        sclk, mclk = get_clocks(hwmon_dir)
                        power, fan = get_power_and_fan(hwmon_dir)

                        gpu_util_history.append(gpu_util)
                        gpu_util_history = gpu_util_history[-HISTORY_LENGTH:]
                        mem_util_history.append(mem_util)
                        mem_util_history = mem_util_history[-HISTORY_LENGTH:]
                        temp_junction_history.append(int(junction_temp))
                        temp_junction_history = temp_junction_history[-HISTORY_LENGTH:]

                        current_line = 4
                        print(term.move_xy(0, current_line) + f"GPU Utilization: {gpu_util}%")
                        current_line += 1
                        print(term.move_xy(0, current_line) + f"Memory Utilization: {mem_util}%")
                        current_line += 1
                        print(term.move_xy(0, current_line) + f"VRAM: {used_vram // 1024 // 1024}MB / {total_vram // 1024 // 1024}MB")
                        current_line += 1
                        print(term.move_xy(0, current_line) + f"Temperatures: Edge={edge_temp}°C, Junction={junction_temp}°C, Memory={mem_temp}°C")
                        current_line += 1
                        print(term.move_xy(0, current_line) + f"Clocks: sclk={sclk}MHz, mclk={mclk}MHz")
                        current_line += 1
                        print(term.move_xy(0, current_line) + f"Power: {power}W, Fan: {fan}RPM")
                        current_line += 2 # Add a blank line for spacing

                        # Draw graphs below the stats
                        graph_height = 8 # Fixed height for graphs
                        graph_start_x = 0 # Starting X position for graphs

                        # GPU Utilization Graph
                        print(term.move_xy(0, current_line) + term.clear_eol + "GPU Utilization History:")
                        current_line += 1
                        print(draw_history_graph(term, gpu_util_history, 100, graph_height, current_line, graph_start_x, term.on_green))
                        current_line += graph_height + 1

                        # Memory Utilization Graph
                        print(term.move_xy(0, current_line) + term.clear_eol + "Memory Utilization History:")
                        current_line += 1
                        print(draw_history_graph(term, mem_util_history, 100, graph_height, current_line, graph_start_x, term.on_blue))
                        current_line += graph_height + 1

                        # Junction Temperature Graph
                        print(term.move_xy(0, current_line) + term.clear_eol + "Junction Temperature History:")
                        current_line += 1
                        print(draw_history_graph(term, temp_junction_history, 120, graph_height, current_line, graph_start_x, term.on_red))
                        current_line += graph_height + 1


                    except FileNotFoundError as e:
                        print(f"Error reading file: {e}. Check if the amdgpu driver is loaded and you have the correct permissions.")
                        break
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        break

                time.sleep(1)
        except KeyboardInterrupt:
            print(term.normal + "\nExiting...")

if __name__ == "__main__":
    main()
