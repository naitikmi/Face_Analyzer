"""
Face Detection Module
Uses MediaPipe's Tasks API (BlazeFace short-range model) for fast face detection.

Note: MediaPipe's older `mp.solutions.face_detection` API is not available on
current Python/platform wheels (it was replaced by the Tasks API), so this
module targets `mediapipe.tasks.python.vision.FaceDetector` instead, backed by
a local `.tflite` model bundle under `models/weights/`.
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
from typing import List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parent / "weights" / "blaze_face_short_range.tflite")


@dataclass
class FaceDetection:
    """Face detection result"""
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    landmarks: Optional[np.ndarray] = None


class FaceDetector:
    """Face detector using MediaPipe's Tasks API"""

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        max_faces: int = 5,
        model_path: str = DEFAULT_MODEL_PATH
    ):
        options = vision.FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=min_detection_confidence,
        )
        self._detector = vision.FaceDetector.create_from_options(options)
        self.max_faces = max_faces

    def detect(self, image: np.ndarray) -> List[FaceDetection]:
        """
        Detect faces in image

        Args:
            image: Input image (BGR or RGB)

        Returns:
            List of FaceDetection objects
        """
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Convert BGR to RGB if needed
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image_rgb))
        result = self._detector.detect(mp_image)

        h, w = image.shape[:2]
        detections = []
        for det in result.detections[:self.max_faces]:
            box = det.bounding_box
            x = max(0, box.origin_x)
            y = max(0, box.origin_y)
            width = min(box.width, w - x)
            height = min(box.height, h - y)
            confidence = det.categories[0].score if det.categories else 0.0

            if width > 0 and height > 0:
                detections.append(FaceDetection(
                    bbox=(x, y, width, height),
                    confidence=confidence
                ))

        return detections

    def detect_and_crop(self, image: np.ndarray, padding: float = 0.2) -> List[Tuple[np.ndarray, FaceDetection]]:
        """
        Detect faces and return cropped face images

        Args:
            image: Input image
            padding: Padding around face as fraction of face size

        Returns:
            List of (cropped_face, detection) tuples
        """
        detections = self.detect(image)
        h, w = image.shape[:2]
        results = []

        for det in detections:
            x, y, width, height = det.bbox

            _x1 = max(0, int(x - width * padding))
            _y1 = max(0, int(y - height * padding))
            _x2 = min(w, int(x + width * (1 + padding)))
            _y2 = min(h, int(y + height * (1 + padding)))

            cropped = image[_y1:_y2, _x1:_x2].copy()

            if cropped.size > 0:
                results.append((cropped, det))

        return results

    def close(self):
        """Release resources"""
        self._detector.close()
