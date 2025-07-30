"""
Module to support working with images, including collections of images.
"""

from pathlib import Path
import os
import logging

import cv2

logger = logging.getLogger(__name__)


def is_supported_image(path: Path) -> bool:
    return path.suffix in [".jpg", ".jpeg", ".png"]


def convert_to(path: Path, output_path: Path):
    """
    Write an image at the input path to the output path. If the extensions
    are different the image will be converted.
    """
    cv2.imwrite(str(output_path), cv2.imread(str(path)))


def extract_video(
    path: Path, output_dir: Path, start_count: int = 0, extension: str = "jpg"
) -> int:
    """
    Extract a video to the provided directory, the frame counter will increment
    for each frame.
    """
    count = start_count

    vidcap = cv2.VideoCapture(str(path))
    success, frame = vidcap.read()
    success = True

    while success:
        success, frame = vidcap.read()
        if not success:
            break
        cv2.imwrite(str(output_dir / f"frame{count:05d}.{extension}"), frame)
        count += 1
    return count


def extract_image_or_video(
    path: Path, output_dir: Path, count: int = 0, extension: str = "jpg"
) -> int:
    """
    Extract the provided entity to the provided path, if it is a video
    then each frame is written as an image.
    """

    if is_supported_image(path):
        convert_to(path, output_dir / f"frame{count:05d}.{extension}")
        return count + 1

    return extract_video(path, output_dir, count, extension)


def extract(path: Path, output_dir: Path, output_extension: str = "jpg"):
    """
    Extract the content at the provided path to the provided
    output directory. It can be a set of images or videos.
    """

    os.makedirs(output_dir, exist_ok=True)

    total_frames = 0
    if not path.is_dir():
        total_frames = extract_image_or_video(
            path, output_dir, extension=output_extension
        )
    else:
        for filename in os.listdir(path):
            total_frames = extract_image_or_video(
                path / filename, output_dir, total_frames, output_extension
            )

    logger.info("Extracted %d frames", total_frames)
