import json 
import requests
config_file = "config.json"

with open(config_file, "r") as f:
    config = json.load(f)

api_endpoint = config.get("control_api")

url = f"http://{config.get("ip")}/{api_endpoint}"

def set_servo(servo_id, value):
    global url
    req_params= {
		"id": servo_id,
		"angle": value
    }
    # TODO: Remove after testing
    try:
      response = requests.get(url, params=req_params) 
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the server: {e}")
        response = None
        return
    print(f"Response: {response.text}")
    print(f"servo {servo_id} to angle {value} ")
