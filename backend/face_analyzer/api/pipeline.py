"""
Orchestrates the full analyze pipeline: face detection -> landmarks ->
face-shape classification -> beard/hair/glasses recommendations.

All models are constructed without a `model_path`, so every stage runs on
the existing geometric/rule-based logic - no trained ONNX weights exist yet,
and none are required for the MVP (see project plan).
"""
import re
from typing import Dict, Optional

import numpy as np

from face_analyzer.models.face_detection import FaceDetector
from face_analyzer.models.face_landmarks import FaceLandmarkDetector
from face_analyzer.models.face_shape import FaceShapeClassifier
from face_analyzer.models.beard_recommender import BeardStyleRecommender
from face_analyzer.models.hair_recommender import HairStyleRecommender
from face_analyzer.models.glasses_recommender import GlassesStyleRecommender
from face_analyzer.models.feature_insights import analyze_features


def slugify(style_name: str) -> str:
    """Convert a style name like 'Van Dyke' into a URL/filename-safe slug."""
    slug = style_name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


_EMPTY_RESULT = {
    "face_detected": False,
    "face_count": 0,
    "face_shape": None,
    "recommendations": None,
    "feature_insights": None,
    "extensions": {"skin_analysis": None, "feedback_submission_url": None},
}


class AnalysisPipeline:
    """Loads every model once and runs the full analyze pipeline per request."""

    def __init__(self):
        self.face_detector = FaceDetector()
        self.landmark_detector = FaceLandmarkDetector()
        self.shape_classifier = FaceShapeClassifier()
        self.beard_recommender = BeardStyleRecommender()
        self.hair_recommender = HairStyleRecommender()
        self.glasses_recommender = GlassesStyleRecommender()

    def analyze(
        self,
        image: np.ndarray,
        gender: Optional[str] = None,
        maintenance_preference: Optional[str] = None,
    ) -> Dict:
        detections = self.face_detector.detect(image)
        face_count = len(detections)

        if face_count == 0:
            return dict(_EMPTY_RESULT, face_count=0)

        landmarks_list = self.landmark_detector.detect(image)
        if not landmarks_list:
            # Two independent MediaPipe models disagreeing is rare but
            # possible (e.g. a borderline-confidence face) - report the
            # face count from the detector but no shape/recommendations.
            return dict(_EMPTY_RESULT, face_count=face_count)

        # Neither detector ranks faces by prominence beyond detection order;
        # take the first (largest/most confident in practice) face and
        # surface face_count so the caller can warn about multiple faces.
        landmarks = landmarks_list[0]
        shape_result = self.shape_classifier.classify(landmarks.landmarks, landmarks.image_shape)
        face_shape = shape_result.shape.value

        preferences = {"maintenance": maintenance_preference} if maintenance_preference else None
        beard_recs = self.beard_recommender.recommend(
            face_shape, face_measurements=shape_result.measurements, user_preferences=preferences
        )
        hair_recs = self.hair_recommender.recommend(
            face_shape, gender=gender, face_measurements=shape_result.measurements
        )
        glasses_recs = self.glasses_recommender.recommend(
            face_shape, face_measurements=shape_result.measurements
        )
        feature_notes = analyze_features(landmarks.landmarks, shape_result.ratios)

        return {
            "face_detected": True,
            "face_count": face_count,
            "face_shape": {
                "shape": face_shape,
                "confidence": round(shape_result.confidence, 3),
                "description": self.shape_classifier.get_shape_description(shape_result.shape),
                "all_scores": {k.value: round(v, 3) for k, v in shape_result.all_scores.items()},
                "measurements": {k: round(v, 2) for k, v in shape_result.measurements.items()},
            },
            "recommendations": {
                "beard": [
                    {
                        "style": r.style,
                        "style_slug": slugify(r.style),
                        "suitability_score": round(r.suitability_score, 3),
                        "description": r.description,
                        "image_url": f"/styles/beard/{slugify(r.style)}.jpg",
                    }
                    for r in beard_recs
                ],
                "hair": [
                    {
                        "style": r.style,
                        "style_slug": slugify(r.style),
                        "suitability_score": round(r.suitability_score, 3),
                        "description": r.description,
                        "gender": r.gender,
                        "image_url": f"/styles/hair/{r.gender}/{slugify(r.style)}.jpg",
                    }
                    for r in hair_recs
                ],
                "glasses": [
                    {
                        "style": r.style,
                        "style_slug": slugify(r.style),
                        "suitability_score": round(r.suitability_score, 3),
                        "description": r.description,
                        "image_url": f"/styles/glasses/{slugify(r.style)}.jpg",
                    }
                    for r in glasses_recs
                ],
            },
            "feature_insights": [
                {
                    "feature": note.feature,
                    "verdict": note.verdict,
                    "observation": note.observation,
                    "tip": note.tip,
                }
                for note in feature_notes
            ],
            "extensions": {"skin_analysis": None, "feedback_submission_url": None},
        }

    def close(self):
        self.face_detector.close()
        self.landmark_detector.close()
