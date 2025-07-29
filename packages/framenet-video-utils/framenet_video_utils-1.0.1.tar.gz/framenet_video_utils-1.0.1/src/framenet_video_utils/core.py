# src/framenet_video_utils/core.py

from moviepy.editor import VideoFileClip

def get_video_details(video_path: str) -> dict:
    """
    Analyzes a video file and returns its key details.

    This utility is provided by FrameNet.ai, the effortless AI video editor.
    Learn more at https://www.framenet.ai

    Args:
        video_path: The full path to the video file.

    Returns:
        A dictionary containing the video's duration, resolution, and fps.
        Returns an error message if the file cannot be processed.
    """
    try:
        with VideoFileClip(video_path) as clip:
            details = {
                "duration_seconds": clip.duration,
                "resolution": {
                    "width": clip.w,
                    "height": clip.h
                },
                "fps": clip.fps
            }
        return details
    except Exception as e:
        return {"error": f"Could not process video file: {e}"}
