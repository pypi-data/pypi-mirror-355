import json

data_file = "data.json"
config_file = "config.json"

def save_to_json(name, servo_values):
    if not name.strip():
        print("Name empty")
        return
    data = {"name": name, "servo_values": servo_values}
    try:
        with open(data_file, "r") as df:
            existing_data = json.load(df)
            # if not isinstance(existing_data, list):
            #     print("Data file is not a list. Reinitializing.")
            #     existing_data = []
    except (FileNotFoundError, json.JSONDecodeError):
        print("Data file not found or invalid. Initializing as an empty list.")
        existing_data = []

    existing_data.append(data)

    with open(data_file, "w") as df:
        json.dump(existing_data, df, indent=4)
    print(f"Saved to {data_file}")


def update_ip(ip):
    print(f"Entered IP: {ip}")
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"{e}")
        data = {}
    data["ip"] = ip  
    with open(config_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Updated ip to {ip} in {config_file}")



