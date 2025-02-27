import os
import json
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.local/share/krita/spacenav_plugin_config.json")

last_logged_values = None
zero_count = 0
last_graph_values = None
graph_zero_count = 0

def debug_print(message, level=1, debug_level=1, force=False):
    if not force and debug_level < level:
        return
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_message = f"[{timestamp}] [Level {level}] {message}"
    print(log_message)  # Console fallback
    try:
        from krita import Krita
        docker = next((d for d in Krita.instance().dockers() if d.objectName() == "spacenavDocker"), None)
        if docker and hasattr(docker, 'log_tab') and docker.log_tab and not docker.log_tab.log_frozen:
            if level == 2 and ("Raw SN inputs" in message or "Motion data stored" in message or "Fetching stored motion data" in message):
                try:
                    values_str = message.split(": ", 1)[1]
                    values = eval(values_str)
                    all_zeros = all(v == 0 for v in values.values())
                    global last_logged_values, zero_count
                    if all_zeros:
                        if last_logged_values == values:
                            zero_count += 1
                            return
                        elif zero_count > 0:
                            docker.log_tab.append_log(f"[{timestamp}] [Level 2] Previous all-zero inputs repeated {zero_count} times")
                            zero_count = 0
                    elif zero_count > 0:
                        docker.log_tab.append_log(f"[{timestamp}] [Level 2] Previous all-zero inputs repeated {zero_count} times")
                        zero_count = 0
                    last_logged_values = values
                    docker.log_tab.append_log(log_message)
                except Exception:
                    docker.log_tab.append_log(log_message)
            elif level == 2 and "Graph updated" in message:
                try:
                    values_str = message.split(": ", 1)[1]
                    x, y, z, r = map(float, values_str.split(", ")[0:4:1])[1::2]
                    values = {"x": x, "y": y, "z": z, "r": r}
                    all_zeros = all(v == 0 for v in values.values())
                    global last_graph_values, graph_zero_count
                    if all_zeros:
                        if last_graph_values == values:
                            graph_zero_count += 1
                            return
                        elif graph_zero_count > 0:
                            docker.log_tab.append_log(f"[{timestamp}] [Level 2] Previous all-zero graph updates repeated {graph_zero_count} times")
                            graph_zero_count = 0
                    elif graph_zero_count > 0:
                        docker.log_tab.append_log(f"[{timestamp}] [Level 2] Previous all-zero graph updates repeated {graph_zero_count} times")
                        graph_zero_count = 0
                    last_graph_values = values
                    docker.log_tab.append_log(log_message)
                except Exception:
                    docker.log_tab.append_log(log_message)
            else:
                docker.log_tab.append_log(log_message)
    except Exception:
        pass  # Silent fail to console

def save_settings(settings):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(settings, f)
        debug_print("Settings saved to " + CONFIG_PATH, 1, debug_level=1)
    except Exception as e:
        debug_print(f"Error saving settings: {e}", 1, debug_level=1)

def load_settings():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                settings = json.load(f)
            debug_print("Settings loaded from " + CONFIG_PATH, 1, debug_level=1)
            return settings
        else:
            debug_print("No config file found, using defaults", 1, debug_level=1)
            return None
    except Exception as e:
        debug_print(f"Error loading settings: {e}", 1, debug_level=1)
        return None
