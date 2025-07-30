# AI Robot Position Finder
[PyPI Page](https://pypi.org/project/ai-robot-position-finder)

![alt text](/images/image.png?raw=true)

![alt text](/images/image2.png)

## Installation

```bash
pip install ai-robot-position-finder
```


**First Time Only**
This app requires a config.json file present in the working directory 
*Which should contain the following* or it can be obtained from [config.json](config.json)

```json
{
    "initial_position_url": "https://github.com/AI-Robot-GCEK/robo-initial-positions/blob/main/src/initial-positions.h",
    "servo_count": 16,
    "control_api": "setServo",
    "ip": ""
}
```
> **Some Things to note**
> - I have provided the initial_positions as a URL, and it is `scraped` using a module called `ai-robot-position-scraper` you can find it [here](https://pypi.org/project/ai-robot-position-scraper/). If you want to change that and want to do something like, provide a list inside the JSON or something create an issue or update the app and send a PR.

## Usage

```bash
ai-ps
```

## update
```bash
pip install --upgrade ai-robot-position-finder
```

## Features
- Initializes the robot position from a URL ✅
- Values can be saved to a file ✅


## Contributing
Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for details on how to contribute to this project.
