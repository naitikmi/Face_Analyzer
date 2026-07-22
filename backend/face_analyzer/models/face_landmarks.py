"""
Face Landmark Detection Module
Uses MediaPipe's Tasks API (FaceLandmarker) for 478-point facial landmark detection
(468 mesh points + 10 iris points).

Note: MediaPipe's older `mp.solutions.face_mesh` API is not available on
current Python/platform wheels (it was replaced by the Tasks API), so this
module targets `mediapipe.tasks.python.vision.FaceLandmarker` instead, backed
by a local `.task` model bundle under `models/weights/`.
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parent / "weights" / "face_landmarker.task")


@dataclass
class FaceLandmarks:
    """Face landmarks result"""
    landmarks: np.ndarray  # Shape: (478, 3) - x, y, z normalized coordinates
    image_shape: Tuple[int, int]  # height, width
    confidence: float


class FaceLandmarkDetector:
    """Face landmark detector using MediaPipe's FaceLandmarker task"""

    def __init__(
        self,
        max_num_faces: int = 5,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
        model_path: str = DEFAULT_MODEL_PATH
    ):
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=max_num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self.max_num_faces = max_num_faces

    def detect(self, image: np.ndarray) -> List[FaceLandmarks]:
        """
        Detect face landmarks in image

        Args:
            image: Input image (BGR or RGB)

        Returns:
            List of FaceLandmarks objects
        """
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image

        h, w = image.shape[:2]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image_rgb))
        result = self._landmarker.detect(mp_image)

        landmarks_list = []
        for face_landmarks in result.face_landmarks[:self.max_num_faces]:
            landmarks = np.array([
                [lm.x, lm.y, lm.z] for lm in face_landmarks
            ])

            landmarks_list.append(FaceLandmarks(
                landmarks=landmarks,
                image_shape=(h, w),
                confidence=1.0
            ))

        return landmarks_list

    def get_key_landmarks(self, landmarks: FaceLandmarks) -> dict:
        """
        Extract key facial landmarks for face shape analysis

        Uses MediaPipe Face Mesh topology indices (0-467 mesh, 468-477 iris):
        - Key points for face shape: forehead, cheekbones, jawline, chin
        """
        lm = landmarks.landmarks

        key_points = {
            'forehead_center': lm[10],  # forehead center
            'left_forehead': lm[103],   # left forehead
            'right_forehead': lm[332],  # right forehead
            'left_cheekbone': lm[116],  # left cheekbone
            'right_cheekbone': lm[345], # right cheekbone
            'left_jaw': lm[172],        # left jaw
            'right_jaw': lm[397],       # right jaw
            'chin': lm[152],            # chin
            'left_eye_center': lm[468] if len(lm) > 468 else lm[159],  # left eye center (iris if available)
            'right_eye_center': lm[473] if len(lm) > 473 else lm[386], # right eye center (iris if available)
            'nose_tip': lm[1],          # nose tip
            'nose_bridge': lm[168],     # nose bridge
            'mouth_left': lm[61],       # mouth left corner
            'mouth_right': lm[291],     # mouth right corner
            'mouth_top': lm[13],        # mouth top
            'mouth_bottom': lm[14],     # mouth bottom
        }

        return key_points

    def close(self):
        """Release resources"""
        self._landmarker.close()
