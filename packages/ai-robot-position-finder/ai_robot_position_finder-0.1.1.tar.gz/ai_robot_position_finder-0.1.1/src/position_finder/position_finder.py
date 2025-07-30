from .gui import gui_main
from position_scraper import extract_positions , extract_names
import json
import click

config_file = "config.json"

with open(config_file, "r") as f:
    config = json.load(f)

url = config.get("initial_position_url")
servo_count = config.get("servo_count", 16)
api_endpoint = config.get("control_api")



esp_ip = config.get("ip")

# format {'LA1_INITIAL_POSITION': 25..}
initial_positions = extract_positions(url)
# format [25, 30,..]
initial_angles = [value for position, value in initial_positions.items()]
# format ['LA1', 'LA2', ...]
servo_names = extract_names(url)

servo_values = {i: initial_angles[i] for i in range(servo_count)}

@click.command()
def run():
    gui_main(servo_count, initial_angles, servo_values, servo_names, esp_ip)


if __name__ == "__main__":
    run()
