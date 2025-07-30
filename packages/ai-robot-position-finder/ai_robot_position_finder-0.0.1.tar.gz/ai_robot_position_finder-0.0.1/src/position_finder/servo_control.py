import json 
import requests
config_file = "config.json"

with open(config_file, "r") as f:
    config = json.load(f)

API_ENDPOINT = config.get("control_api")

URL = f"http://{config.get("ip")}/{API_ENDPOINT}"

def set_servo(servo_id, value):
    req_params= {
		"id": servo_id,
		"position": value
    }
    url = f"{URL}"  
    # TODO: Remove after testing
    # response = requests.get(URL, params=req_params)

    # print(f"Response: {response.text}")
    print(f"servo {servo_id} to value {value} ")
