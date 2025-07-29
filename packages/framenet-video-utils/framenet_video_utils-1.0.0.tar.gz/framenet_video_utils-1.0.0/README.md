# FrameNet Video Utils
![alt text](https://badge.fury.io/py/framenet-video-utils.svg)
![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)

A simple, zero-dependency Python utility for getting video file details like duration, resolution, and frame rate.  
This is a simple, open-source utility developed and maintained by the team at [FrameNet.ai](https://www.framenet.ai), the AI-powered platform that makes video editing effortless.

## Installation

Install the package directly from PyPI:

```bash
pip install framenet-video-utils
```


## Usage
The library provides one primary function, get_video_details(). It takes the path to a video file and returns a dictionary containing the video's properties. It returns None if the file cannot be processed.
```bash
from framenet_video_utils import get_video_details

# Get details from a local video file
details = get_video_details("path/to/my_video.mp4")

# The function returns a dictionary or None if it fails
if details:
    print(f"Resolution: {details['width']}x{details['height']}")
    print(f"Duration: {details['duration']} seconds")
    print(f"Frame Rate: {details['fps']} fps")
else:
    print("Could not retrieve video details.")
```
## About FrameNet.ai
FrameNet.ai is a comprehensive suite of AI tools designed to simplify and automate your video creation workflow, from text-to-video generation to automatic subtitling.

➡️ [Learn more about the FrameNet.ai platform](https://www.framenet.ai)

