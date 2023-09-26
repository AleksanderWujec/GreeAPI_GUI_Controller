import tkinter as tk
from tkinter import ttk, messagebox, font, Button
import asyncio
import logging
from greeclimate.discovery import Discovery
from greeclimate.device import Device, Mode, FanSpeed

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
for lib in ['greeclimate', 'asyncio']:
    lib_logger = logging.getLogger(lib)
    lib_logger.handlers.clear()
    lib_logger.setLevel(logging.INFO)
    lib_logger.propagate = True
device = None


async def init_device():
    global device
    discovery = Discovery()
    for device_info in await discovery.scan(wait_for=5):
        try:
            device = Device(device_info)
            await device.bind()
            device.xfan = True  # Enable xfan function
            await device.push_state_update()  # Update device state
        except:
            _LOGGER.error("Unable to bind to gree device: %s", device_info)
            continue
    if not device:
        print("No GREE devices found.")
        return
    await device.update_state()


def update_info():
    if device:
        info_var.set(
            f"Current set temperature: {device.target_temperature}°C\n"
            f"Current temperature: {device.current_temperature}°C\n"
            f"Current humidity: {device.current_humidity}%\n"  # Added humidity info
            f"Device status: {'on' if device.power else 'off'}\n"
            f"Operating mode: {device.mode}"
        )
    else:
        info_var.set("Device not found.")


def set_fan_speed(speed_str):
    global device
    if device:
        speeds_mapping = {
            "auto": FanSpeed.Auto,
            "low": FanSpeed.Low,
            "medium": FanSpeed.Medium,
            "high": FanSpeed.High
        }
        speed_value = speeds_mapping.get(speed_str)
        if speed_value is not None:
            device.fan_speed = speed_value
            asyncio.run(device.push_state_update())
            update_info()


def set_mode(mode_str):
    global device
    if device:
        modes_mapping = {
            "auto": Mode.Auto,
            "cooling": Mode.Cool,
            "drying": Mode.Dry,
            "fan": Mode.Fan,
            "heating": Mode.Heat
        }
        mode_value = modes_mapping.get(mode_str)
        if mode_value is not None:
            device.mode = mode_value
            asyncio.run(device.push_state_update())
            update_info()


def toggle_power():
    global device
    if device:
        device.power = not device.power
        asyncio.run(device.push_state_update())
        update_info()


def increase_temperature():
    global device
    if device:
        new_temp = min(device.target_temperature + 1, 30)  # limit to 30°C
        device.target_temperature = new_temp
        asyncio.run(device.push_state_update())
        update_info()
        temp_label_var.set(f"Temperature: {new_temp}°C")


def decrease_temperature():
    global device
    if device:
        new_temp = max(device.target_temperature - 1, 16)  # limit to 16°C
        device.target_temperature = new_temp
        asyncio.run(device.push_state_update())
        update_info()
        temp_label_var.set(f"Temperature: {new_temp}°C")


def set_temperature(val):
    global device
    if device:
        device.target_temperature = int(float(val))
        asyncio.run(device.push_state_update())
        update_info()
        temp_label_var.set(f"Temperature: {val}°C")


def periodic_update():
    asyncio.run(device.update_state())
    update_info()
    root.after(60000, periodic_update)  # 60000 ms = 1 minute


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(init_device())


def create_custom_button(parent, text, command=None):
    """Function to create a customized button."""
    btn = tk.Button(parent, text=text, command=command, font=("Arial", 12),
                    bg="#4E94CE", fg="white", activebackground="#3C7CB0",
                    activeforeground="white", bd=2, relief="raised", padx=10, pady=2)
    btn.bind("<ButtonPress-1>", lambda e: e.widget.config(relief="sunken"))
    btn.bind("<ButtonRelease-1>", lambda e: e.widget.config(relief="raised"))
    return btn


root = tk.Tk()
root.title("GREE Control Panel")

frame = tk.Frame(root, padx=20, pady=20)
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

info_var = tk.StringVar()
info_label = tk.Label(frame, textvariable=info_var, font=("Arial", 14))
info_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

power_btn = create_custom_button(frame, text="Turn On/Off", command=toggle_power)
power_btn.grid(row=1, column=0, pady=10, sticky=tk.W)

mode_label = tk.Label(frame, text="Operating Mode:", font=("Arial", 12))
mode_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 10))
mode_combo = ttk.Combobox(frame, values=["auto", "cooling", "fan", "heating"], width=15, font=("Arial", 10))
mode_combo.grid(row=1, column=2, pady=10, padx=(0, 20))
mode_combo.bind("<<ComboboxSelected>>", lambda _: set_mode(mode_combo.get()))

temp_label_var = tk.StringVar(value=f"Temperature: {device.target_temperature if device else 25}°C")
temp_label = tk.Label(frame, textvariable=temp_label_var, font=("Arial", 12))
temp_label.grid(row=2, column=1, sticky=tk.W, padx=(0, 10))

decrease_temp_btn = create_custom_button(frame, text="-", command=decrease_temperature)
decrease_temp_btn.grid(row=2, column=2, pady=10, padx=(0, 5))

increase_temp_btn = create_custom_button(frame, text="+", command=increase_temperature)
increase_temp_btn.grid(row=2, column=3, pady=10, padx=(5, 20))

fan_speed_label = tk.Label(frame, text="Fan Speed:", font=("Arial", 12))
fan_speed_label.grid(row=3, column=1, sticky=tk.W, padx=(0, 10))
fan_speed_combo = ttk.Combobox(frame, values=["auto", "low", "medium", "high"], width=15, font=("Arial", 10))
fan_speed_combo.grid(row=3, column=2, pady=10, padx=(0, 20))
fan_speed_combo.bind("<<ComboboxSelected>>", lambda _: set_fan_speed(fan_speed_combo.get()))

periodic_update()
update_info()
root.mainloop()
