import tkinter as tk
from .servo_control import set_servo , re_initialize_servos
from .data import save_to_json , update_ip
import json 
import click


def create_servo_slider(frame, servo_id, initial_value,slider_label):
    def on_move(val):
        # set_position when slider moves 
        # TODO: check if this creates too many requests
        set_servo(servo_id, int(val))

    slider = tk.Scale(
        frame,
        from_=0,
        to=180,
        orient=tk.HORIZONTAL,
        label=f"Servo: {slider_label} ",
        command=on_move,
    )
    # Set the initial value of the slider , from github
    slider.set(initial_value) 
    return slider

def gui_main(SERVO_COUNT, initial_angles, servo_values, servo_names, esp_ip):
    global ip_entry  
    root = tk.Tk()
    root.title("AI-Robot-PFv0.1")
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    sliders_frame = tk.Frame(root)
    sliders_frame.pack(padx=10, pady=10)
    
    # HACK: TODO: refactor this.
    # Toggle slider/input functionality
    # Dictionary to store grid positions of sliders
    slider_positions = {}

    

    def toggle_slider_input(idx):
        slider = sliders[idx]
        if isinstance(slider, tk.Scale):
            # Store the current grid position
            slider_positions[idx] = slider.grid_info()
            # Replace slider with Entry
            value = slider.get()
            slider.grid_forget()
            entry_frame = tk.Frame(sliders_frame)
            entry_frame.grid(row=slider_positions[idx]['row'], column=slider_positions[idx]['column'], padx=5, pady=5)
            label = tk.Label(entry_frame, text=f"Servo: {servo_names[idx]}")
            label.pack(side=tk.LEFT)
            entry = tk.Entry(entry_frame, width=5)
            entry.insert(0, str(value))
            entry.pack(side=tk.RIGHT)
            def on_entry_confirm(event=None):
                try:
                    val = int(entry.get())
                    if 0 <= val <= 180:
                        set_servo(idx, val)
                        # Update the slider value but keep the input box
                        slider.set(val)
                except ValueError:
                    pass
            entry.bind('<Return>', on_entry_confirm)
            sliders[idx] = entry_frame
        else:
            # Replace Entry with slider
            try:
                val = int(slider.get())
            except Exception:
                val = initial_angles[idx]
            slider.grid_forget()
            new_slider = create_servo_slider(sliders_frame, idx, val, servo_names[idx])
            new_slider.grid(row=slider_positions[idx]['row'], column=slider_positions[idx]['column'])
            sliders[idx] = new_slider

    def toggle_all_sliders():
        for idx in range(SERVO_COUNT):
            toggle_slider_input(idx)

    # Add a single button to toggle all sliders
    toggle_all_button = tk.Button(frame, text="Toggle All", command=toggle_all_sliders)
    toggle_all_button.grid(row=0, column=4, padx=5)

    # Initialize button 
    def on_initialize():
        re_initialize_servos(initial_angles)
        # reset the sliders
        for i, slider in enumerate(sliders):
            slider.set(initial_angles[i])

    initialize_button = tk.Button(
        frame, 
        text="Initialize", 
        command=on_initialize
    )
    initialize_button.grid(row=0, column=3, padx=5)
    # Set initial values for servos


    # IP entry
    ip_label = tk.Label(frame, text="Server IP:")
    ip_label.grid(row=0, column=0, padx=5)
    ip_entry = tk.Entry(frame)
    ip_entry.grid(row=0, column=1, padx=5)
    # set initial value of ip from the config 
    ip_button = tk.Button(frame, text="Set IP", command=lambda: update_ip(ip_entry.get()))
    ip_button.grid(row=0, column=2, padx=5)
    ip_entry.insert(0, esp_ip)

    # Name entry and save button
    name_label = tk.Label(frame, text="Name:")
    name_label.grid(row=1, column=0, padx=5)
    name_entry = tk.Entry(frame)
    name_entry.grid(row=1, column=1, padx=5)
    save_button = tk.Button(
        frame, 
        text="Save values", 
        command=lambda: save_to_json(name_entry.get(),servo_values)  
    )
    save_button.grid(row=1, column=2, padx=5)


    # Arrange sliders in a 4x4 grid
    sliders = []
    for id in range(SERVO_COUNT):
        slider = create_servo_slider(sliders_frame, id, initial_angles[id], servo_names[id])
        sliders.append(slider)
        row, col = divmod(id, 4)  # Calculate row and column for 4x4 grid
        slider.grid(row=row, column=col, padx=5, pady=5)  # Use grid for layout

    root.mainloop()
