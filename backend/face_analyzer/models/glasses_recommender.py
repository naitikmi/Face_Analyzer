"""
Glasses Style Recommender Module
Recommends eyeglass frame styles based on face shape
"""
import numpy as np
import yaml
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import onnxruntime as ort


DEFAULT_CONFIG_PATH = str(Path(__file__).resolve().parents[2] / "config.yaml")


@dataclass
class GlassesRecommendation:
    """Glasses style recommendation result"""
    style: str
    confidence: float
    description: str
    style_category: str
    suitability_score: float


class GlassesStyleRecommender:
    """Recommends eyeglass frame styles based on face shape and facial features"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_path: Optional[str] = None):
        self.config_path = Path(config_path)
        self.model_path = model_path
        self.session = None

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.glasses_styles = self.config.get('GLASSES_STYLES', {})
        self.face_shapes = self.config.get('FACE_SHAPES', [])

        if model_path:
            self.session = ort.InferenceSession(model_path)
            self.input_name = self.session.get_inputs()[0].name

    def get_styles_for_shape(self, face_shape: str) -> List[str]:
        """Get predefined glasses styles for a face shape"""
        return self.glasses_styles.get(face_shape.lower(), [])

    def get_style_descriptions(self) -> Dict[str, Dict]:
        """Get detailed descriptions for all glasses frame styles"""
        return {
            "rectangular frames": {
                "description": "Clean, angular frames wider than they are tall",
                "style_category": "Classic - versatile, professional look",
                "best_for": ["oval", "round"]
            },
            "square frames": {
                "description": "Bold, sharp-cornered frames with strong structure",
                "style_category": "Bold - adds definition to soft features",
                "best_for": ["oval", "round", "oblong"]
            },
            "aviator": {
                "description": "Teardrop-shaped frames with thin metal rims",
                "style_category": "Classic - relaxed, retro-cool look",
                "best_for": ["oval", "square", "heart", "triangle"]
            },
            "browline": {
                "description": "Bold upper rim with thinner bottom half, retro-inspired",
                "style_category": "Bold - emphasizes the brow line",
                "best_for": ["oval", "round", "diamond", "oblong", "triangle"]
            },
            "wayfarer": {
                "description": "Trapezoidal frames with a flat top bar",
                "style_category": "Classic - everyday casual look",
                "best_for": ["oval", "round", "oblong"]
            },
            "round frames": {
                "description": "Circular lenses with soft, curved edges",
                "style_category": "Soft - counters strong angular jawlines",
                "best_for": ["square", "heart", "diamond", "oblong"]
            },
            "oval frames": {
                "description": "Gently rounded frames wider than tall, softly balanced",
                "style_category": "Soft - understated, balanced look",
                "best_for": ["square", "heart", "diamond", "triangle"]
            },
            "rimless": {
                "description": "Lightweight lenses with minimal or no frame border",
                "style_category": "Minimal - subtle, lightweight look",
                "best_for": ["square", "heart", "diamond", "triangle"]
            },
            "cat-eye": {
                "description": "Upswept outer corners that lift and widen the upper face",
                "style_category": "Statement - adds width above the cheekbones",
                "best_for": ["square", "heart", "diamond", "triangle"]
            },
            "geometric frames": {
                "description": "Angular, multi-sided frames (hexagonal, octagonal shapes)",
                "style_category": "Statement - modern, fashion-forward look",
                "best_for": ["round"]
            },
            "oversized frames": {
                "description": "Large frames that add visual width and presence",
                "style_category": "Statement - balances an elongated face",
                "best_for": ["oblong"]
            },
        }

    def recommend(
        self,
        face_shape: str,
        face_measurements: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> List[GlassesRecommendation]:
        """
        Recommend glasses styles for given face shape

        Args:
            face_shape: Detected face shape
            face_measurements: Optional facial measurements for fine-tuning
            user_preferences: Optional user preferences (boldness, etc.)

        Returns:
            List of GlassesRecommendation sorted by suitability
        """
        styles = self.get_styles_for_shape(face_shape)
        descriptions = self.get_style_descriptions()

        recommendations = []
        for style in styles:
            desc = descriptions.get(style, {})

            suitability = self._calculate_suitability(
                style, face_shape, face_measurements, user_preferences
            )

            recommendations.append(GlassesRecommendation(
                style=style,
                confidence=suitability,
                description=desc.get("description", ""),
                style_category=desc.get("style_category", "Unknown"),
                suitability_score=suitability
            ))

        if self.session is not None and face_measurements:
            ml_scores = self._ml_predict(face_shape, face_measurements)
            for rec in recommendations:
                if rec.style in ml_scores:
                    rec.confidence = (rec.confidence + ml_scores[rec.style]) / 2
                    rec.suitability_score = rec.confidence

        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
        return recommendations

    def _calculate_suitability(
        self,
        style: str,
        face_shape: str,
        measurements: Optional[Dict],
        preferences: Optional[Dict]
    ) -> float:
        """Calculate suitability score for a glasses style"""
        base_score = 0.7

        descriptions = self.get_style_descriptions()
        style_info = descriptions.get(style, {})
        best_for = style_info.get("best_for", [])

        if face_shape.lower() in best_for:
            base_score += 0.2

        if measurements:
            cheekbone_width = measurements.get('cheekbone_width', 0)
            face_width = measurements.get('face_width', 0)

            # Wider cheekbones/face can carry bolder, larger frames
            if face_width > 0 and cheekbone_width / face_width > 0.9:
                if style in ("oversized frames", "square frames", "geometric frames"):
                    base_score += 0.1

        if preferences:
            boldness_pref = preferences.get("boldness", "medium").lower()
            style_category = style_info.get("style_category", "").lower()

            if boldness_pref == "bold" and "bold" in style_category:
                base_score += 0.1
            elif boldness_pref == "bold" and "statement" in style_category:
                base_score += 0.1
            elif boldness_pref == "subtle" and "minimal" in style_category:
                base_score += 0.1
            elif boldness_pref == "subtle" and "soft" in style_category:
                base_score += 0.05

        return min(base_score, 1.0)

    def _ml_predict(
        self,
        face_shape: str,
        measurements: Dict
    ) -> Dict[str, float]:
        """Use ML model for prediction if available"""
        try:
            feature_vector = self._prepare_ml_features(face_shape, measurements)
            input_tensor = feature_vector.reshape(1, -1).astype(np.float32)
            outputs = self.session.run(None, {self.input_name: input_tensor})
            probs = outputs[0][0]

            style_list = list(self.get_style_descriptions().keys())
            return {style_list[i]: float(probs[i]) for i in range(len(style_list))}
        except Exception:
            return {}

    def _prepare_ml_features(self, face_shape: str, measurements: Dict) -> np.ndarray:
        """Prepare feature vector for ML model"""
        shape_encoding = np.zeros(len(self.face_shapes))
        if face_shape.lower() in self.face_shapes:
            shape_encoding[self.face_shapes.index(face_shape.lower())] = 1

        measurement_features = np.array([
            measurements.get('face_width', 0),
            measurements.get('face_height', 0),
            measurements.get('forehead_width', 0),
            measurements.get('jaw_width', 0),
            measurements.get('cheekbone_width', 0),
        ], dtype=np.float32)

        return np.concatenate([shape_encoding, measurement_features])

    def get_all_styles(self) -> List[str]:
        """Get all available glasses styles"""
        return list(self.get_style_descriptions().keys())


class GlassesStyleAnalyzer:
    """High-level glasses style analysis"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_path: Optional[str] = None):
        self.recommender = GlassesStyleRecommender(config_path, model_path)
        self.descriptions = self.recommender.get_style_descriptions()

    def analyze(
        self,
        face_shape: str,
        measurements: Optional[Dict] = None,
        preferences: Optional[Dict] = None
    ) -> List[GlassesRecommendation]:
        """Complete glasses style analysis"""
        return self.recommender.recommend(face_shape, measurements, preferences)

    def get_style_details(self, style: str) -> Dict:
        """Get detailed information about a specific style"""
        return self.descriptions.get(style, {})
