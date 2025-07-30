from .gui import gui_main
from position_scraper import extract_positions , extract_names
import json
import click

config_file = "config.json"

with open(config_file, "r") as f:
    config = json.load(f)

URL = config.get("initial_position_url")
SERVO_COUNT = config.get("servo_count", 16)
API_ENDPOINT = config.get("control_api")

initial_positions = extract_positions(URL)
initial_angles = [value for position, value in initial_positions.items()]
servo_names = extract_names(URL)
servo_values = {i: initial_angles[i] for i in range(SERVO_COUNT)}

@click.command()
def run():
    gui_main(SERVO_COUNT,initial_angles,servo_values,servo_names)


if __name__ == "__main__":
    run()
