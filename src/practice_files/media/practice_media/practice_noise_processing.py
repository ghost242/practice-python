import cv2 as cv
import numpy as np


def load_video(video_path: str) -> np.ndarray:
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    return frames


def main():
    pass


if __name__ == "__main__":
    main()
