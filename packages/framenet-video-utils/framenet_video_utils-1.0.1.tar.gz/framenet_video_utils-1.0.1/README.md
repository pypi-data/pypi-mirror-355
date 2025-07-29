# FrameNet Video Utils

![PyPI Version](https://img.shields.io/pypi/v/framenet-video-utils) ![License](https://img.shields.io/pypi/l/framenet-video-utils)

A simple Python utility for getting video file details like duration, resolution, and frame rate.

This package provides a single, easy-to-use function to quickly analyze local video files, which is a common task in any video processing or automation workflow.

---

### About FrameNet.ai

This utility is proudly developed and maintained by the team at **[FrameNet.ai](https://www.framenet.ai)**. Our mission is to make video creation effortless through powerful, AI-driven tools.

While this package helps developers work with video programmatically, our platform offers a full suite of free tools for creators, including:

*   **[Free Online Video Editor](https://www.framenet.ai/tools/video-editor):** A powerful, browser-based editor to cut, merge, and enhance your videos.
*   **[Free Subtitle Generator](https://www.framenet.ai/tools/free-subtitle-generator):** Automatically generate subtitles for your videos with our AI, and export them for free.

This package is part of our commitment to supporting the developer and creator communities.

---

### Installation

Install the package directly from PyPI:

```bash
pip install framenet-video-utils
```

## Usage
The library provides one primary function, get_video_details(). It takes the path to a video file and returns a dictionary containing the video's properties.

```bash
from framenet_video_utils import get_video_details

# Get details from a local video file
video_details = get_video_details("path/to/my_video.mp4")

if video_details and "error" not in video_details:
    print(f"Duration: {video_details['duration_seconds']}s")
    print(f"Resolution: {video_details['resolution']['width']}x{video_details['resolution']['height']}")
    print(f"Frame Rate: {video_details['fps']} fps")
else:
    print(f"Could not process video: {video_details.get('error')}")
```
## About FrameNet.ai
FrameNet.ai is a comprehensive suite of AI tools designed to simplify and automate your video creation workflow, from text-to-video generation to automatic subtitling.

➡️ [Learn more about the FrameNet.ai platform](https://www.framenet.ai)

