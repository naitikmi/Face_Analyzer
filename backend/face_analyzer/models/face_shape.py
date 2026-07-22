"""
Face Shape Classifier Module
Classifies face shape based on facial landmarks
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import onnxruntime as ort
import cv2


class FaceShape(Enum):
    OVAL = "oval"
    ROUND = "round"
    SQUARE = "square"
    HEART = "heart"
    DIAMOND = "diamond"
    OBLONG = "oblong"
    TRIANGLE = "triangle"


@dataclass
class FaceShapeResult:
    """Face shape classification result"""
    shape: FaceShape
    confidence: float
    all_scores: Dict[FaceShape, float]
    measurements: Dict[str, float]


class FaceShapeClassifier:
    """Face shape classifier using geometric analysis and ML model"""
    
    FACE_SHAPES = [
        FaceShape.OVAL,
        FaceShape.ROUND,
        FaceShape.SQUARE,
        FaceShape.HEART,
        FaceShape.DIAMOND,
        FaceShape.OBLONG,
        FaceShape.TRIANGLE
    ]
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.session = None
        if model_path:
            self.session = ort.InferenceSession(model_path)
            self.input_name = self.session.get_inputs()[0].name
    
    def extract_features(self, landmarks: np.ndarray, image_shape: Tuple[int, int]) -> np.ndarray:
        """
        Extract geometric features from landmarks for face shape classification
        
        Args:
            landmarks: Face landmarks array (468, 3)
            image_shape: (height, width) of original image
            
        Returns:
            Feature vector for classification
        """
        h, w = image_shape
        lm = landmarks * np.array([w, h, max(w, h)])
        
        key_points = {
            'forehead_center': lm[10],
            'left_forehead': lm[103],
            'right_forehead': lm[332],
            'left_cheekbone': lm[116],
            'right_cheekbone': lm[345],
            'left_jaw': lm[172],
            'right_jaw': lm[397],
            'chin': lm[152],
            'nose_tip': lm[1],
            'nose_bridge': lm[168],
            'mouth_left': lm[61],
            'mouth_right': lm[291],
            'mouth_top': lm[13],
            'mouth_bottom': lm[14],
        }
        
        measurements = {}
        
        face_width = np.linalg.norm(key_points['left_cheekbone'][:2] - key_points['right_cheekbone'][:2])
        measurements['face_width'] = face_width
        
        face_height = np.linalg.norm(key_points['forehead_center'][:2] - key_points['chin'][:2])
        measurements['face_height'] = face_height
        
        forehead_width = np.linalg.norm(key_points['left_forehead'][:2] - key_points['right_forehead'][:2])
        measurements['forehead_width'] = forehead_width
        
        jaw_width = np.linalg.norm(key_points['left_jaw'][:2] - key_points['right_jaw'][:2])
        measurements['jaw_width'] = jaw_width
        
        cheekbone_width = np.linalg.norm(key_points['left_cheekbone'][:2] - key_points['right_cheekbone'][:2])
        measurements['cheekbone_width'] = cheekbone_width
        
        chin_to_mouth = np.linalg.norm(key_points['chin'][:2] - key_points['mouth_bottom'][:2])
        measurements['chin_to_mouth'] = chin_to_mouth
        
        mouth_width = np.linalg.norm(key_points['mouth_left'][:2] - key_points['mouth_right'][:2])
        measurements['mouth_width'] = mouth_width
        
        nose_to_chin = np.linalg.norm(key_points['nose_tip'][:2] - key_points['chin'][:2])
        measurements['nose_to_chin'] = nose_to_chin
        
        forehead_to_nose = np.linalg.norm(key_points['forehead_center'][:2] - key_points['nose_bridge'][:2])
        measurements['forehead_to_nose'] = forehead_to_nose
        
        ratios = {}
        ratios['height_width_ratio'] = face_height / face_width if face_width > 0 else 0
        ratios['forehead_face_ratio'] = forehead_width / face_width if face_width > 0 else 0
        ratios['jaw_face_ratio'] = jaw_width / face_width if face_width > 0 else 0
        ratios['cheekbone_face_ratio'] = cheekbone_width / face_width if face_width > 0 else 0
        ratios['chin_mouth_height_ratio'] = chin_to_mouth / face_height if face_height > 0 else 0
        ratios['mouth_face_ratio'] = mouth_width / face_width if face_width > 0 else 0
        ratios['nose_chin_face_ratio'] = nose_to_chin / face_height if face_height > 0 else 0
        ratios['forehead_nose_face_ratio'] = forehead_to_nose / face_height if face_height > 0 else 0
        ratios['jaw_forehead_ratio'] = jaw_width / forehead_width if forehead_width > 0 else 0
        ratios['cheekbone_jaw_ratio'] = cheekbone_width / jaw_width if jaw_width > 0 else 0
        
        feature_vector = np.array([
            measurements['face_width'],
            measurements['face_height'],
            measurements['forehead_width'],
            measurements['jaw_width'],
            measurements['cheekbone_width'],
            measurements['chin_to_mouth'],
            measurements['mouth_width'],
            measurements['nose_to_chin'],
            measurements['forehead_to_nose'],
            ratios['height_width_ratio'],
            ratios['forehead_face_ratio'],
            ratios['jaw_face_ratio'],
            ratios['cheekbone_face_ratio'],
            ratios['chin_mouth_height_ratio'],
            ratios['mouth_face_ratio'],
            ratios['nose_chin_face_ratio'],
            ratios['forehead_nose_face_ratio'],
            ratios['jaw_forehead_ratio'],
            ratios['cheekbone_jaw_ratio'],
        ], dtype=np.float32)
        
        return feature_vector, measurements, ratios
    
    def classify_geometric(self, features: np.ndarray, ratios: Dict[str, float]) -> Tuple[FaceShape, float, Dict[FaceShape, float]]:
        """
        Classify face shape using geometric rules based on facial ratios
        """
        scores = {shape: 0.0 for shape in self.FACE_SHAPES}
        
        hw_ratio = ratios.get('height_width_ratio', 0)
        fw_ratio = ratios.get('forehead_face_ratio', 0)
        jw_ratio = ratios.get('jaw_face_ratio', 0)
        cw_ratio = ratios.get('cheekbone_face_ratio', 0)
        jf_ratio = ratios.get('jaw_forehead_ratio', 0)
        cj_ratio = ratios.get('cheekbone_jaw_ratio', 0)
        
        if 1.3 <= hw_ratio <= 1.5 and 0.85 <= fw_ratio <= 1.0 and 0.85 <= jw_ratio <= 1.0:
            scores[FaceShape.OVAL] = 0.9
        elif hw_ratio < 1.2 and fw_ratio > 0.9 and jw_ratio > 0.85:
            scores[FaceShape.ROUND] = 0.85
        elif 0.95 <= hw_ratio <= 1.15 and fw_ratio > 0.9 and jw_ratio > 0.9:
            scores[FaceShape.SQUARE] = 0.9
        elif fw_ratio > 1.0 and jw_ratio < 0.8 and hw_ratio > 1.2:
            scores[FaceShape.HEART] = 0.85
        elif cw_ratio > 0.95 and fw_ratio < 0.9 and jw_ratio < 0.85 and hw_ratio > 1.3:
            scores[FaceShape.DIAMOND] = 0.85
        elif hw_ratio > 1.5 and 0.85 <= fw_ratio <= 1.0 and 0.85 <= jw_ratio <= 1.0:
            scores[FaceShape.OBLONG] = 0.85
        elif fw_ratio > 0.95 and jw_ratio < 0.85 and cw_ratio < 0.9:
            scores[FaceShape.TRIANGLE] = 0.8
        
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        else:
            # No rule matched decisively; fall back to a uniform distribution
            # rather than leaving every score at zero.
            uniform = 1.0 / len(scores)
            scores = {k: uniform for k in scores}

        best_shape = max(scores, key=scores.get)
        confidence = scores[best_shape]
        
        return best_shape, confidence, scores
    
    def classify(self, landmarks: np.ndarray, image_shape: Tuple[int, int]) -> FaceShapeResult:
        """
        Classify face shape from landmarks
        
        Args:
            landmarks: Face landmarks array (468, 3) normalized
            image_shape: (height, width) of original image
            
        Returns:
            FaceShapeResult with classification
        """
        features, measurements, ratios = self.extract_features(landmarks, image_shape)
        
        if self.session is not None:
            input_tensor = features.reshape(1, -1).astype(np.float32)
            outputs = self.session.run(None, {self.input_name: input_tensor})
            probs = outputs[0][0]
            
            scores = {shape: float(probs[i]) for i, shape in enumerate(self.FACE_SHAPES)}
            best_idx = np.argmax(probs)
            best_shape = self.FACE_SHAPES[best_idx]
            confidence = float(probs[best_idx])
        else:
            best_shape, confidence, scores = self.classify_geometric(features, ratios)
        
        return FaceShapeResult(
            shape=best_shape,
            confidence=confidence,
            all_scores=scores,
            measurements=measurements
        )
    
    def get_shape_description(self, shape: FaceShape) -> str:
        """Get human-readable description of face shape"""
        descriptions = {
            FaceShape.OVAL: "Oval face - balanced proportions, slightly longer than wide",
            FaceShape.ROUND: "Round face - similar width and height, soft angles",
            FaceShape.SQUARE: "Square face - similar width and height, strong jawline",
            FaceShape.HEART: "Heart face - wider forehead, narrow chin",
            FaceShape.DIAMOND: "Diamond face - narrow forehead and jaw, wide cheekbones",
            FaceShape.OBLONG: "Oblong face - longer than wide, straight sides",
            FaceShape.TRIANGLE: "Triangle face - wide jawline, narrow forehead",
        }
        return descriptions.get(shape, "Unknown face shape")


class FaceShapeAnalyzer:
    """High-level face shape analysis combining detection and classification"""
    
    def __init__(
        self,
        landmark_detector=None,
        shape_classifier: FaceShapeClassifier = None
    ):
        from face_analyzer.models.face_landmarks import FaceLandmarkDetector
        from face_analyzer.models.face_detection import FaceDetector
        
        self.face_detector = FaceDetector()
        self.landmark_detector = landmark_detector or FaceLandmarkDetector()
        self.shape_classifier = shape_classifier or FaceShapeClassifier()
    
    def analyze(self, image: np.ndarray) -> List[FaceShapeResult]:
        """
        Complete face shape analysis pipeline

        Runs landmark detection directly on the full image rather than on a
        cropped face region: MediaPipe FaceMesh performs its own face
        localization internally, and a crop based on the (unpadded) face
        detector bbox tends to cut off the forehead, which the shape
        classifier depends on heavily (forehead width ratios).  Detecting on
        the full image also means landmarks come back already normalized to
        image coordinates, so no manual rescaling is needed.

        Args:
            image: Input image (BGR)

        Returns:
            List of FaceShapeResult for each detected face
        """
        landmarks_list = self.landmark_detector.detect(image)
        results = []

        for landmarks in landmarks_list:
            shape_result = self.shape_classifier.classify(
                landmarks.landmarks,
                landmarks.image_shape
            )
            results.append(shape_result)

        return results
    
    def close(self):
        """Release resources"""
        self.face_detector.close()
        self.landmark_detector.close()