"""
Hairstyle Recommender Module
Recommends hairstyles based on face shape and gender
"""
import numpy as np
import yaml
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import onnxruntime as ort


DEFAULT_CONFIG_PATH = str(Path(__file__).resolve().parents[2] / "config.yaml")


@dataclass
class HairRecommendation:
    """Hairstyle recommendation result"""
    style: str
    confidence: float
    description: str
    maintenance_level: str
    gender: str
    suitability_score: float


class HairStyleRecommender:
    """Recommends hairstyles based on face shape, gender, and facial features"""

    # Descriptions/maintenance for every style name present in config.yaml's
    # HAIR_STYLES map. best_for is intentionally NOT duplicated here - it is
    # derived directly from HAIR_STYLES at scoring time so the two can never
    # drift out of sync.
    STYLE_INFO = {
        # Male styles
        "textured crop": {"description": "Short, choppy top with tapered sides", "maintenance": "Low - easy to style"},
        "side part": {"description": "Classic parted style, neat and polished", "maintenance": "Medium - daily styling"},
        "pompadour": {"description": "Voluminous swept-back top with tapered sides", "maintenance": "Medium - needs product and styling"},
        "quiff": {"description": "Short sides with textured, swept-up volume on top", "maintenance": "Medium - daily styling"},
        "buzz cut": {"description": "Very short, uniform length all over", "maintenance": "Very Low - minimal styling, frequent trims"},
        "textured quiff": {"description": "Quiff with extra texture for a softer silhouette", "maintenance": "Medium - daily styling"},
        "side sweep": {"description": "Longer top swept to one side", "maintenance": "Low - minimal daily effort"},
        "faux hawk": {"description": "Tapered sides with raised center volume, subtler than a mohawk", "maintenance": "Medium - daily styling"},
        "angular fringe": {"description": "Sharp, angled fringe across the forehead", "maintenance": "Medium - regular trims to keep the line sharp"},
        "taper fade": {"description": "Gradual shortening from top to skin at the sides", "maintenance": "Medium - regular barber visits"},
        "messy fringe": {"description": "Deliberately tousled fringe with textured ends", "maintenance": "Low - minimal styling"},
        "crew cut": {"description": "Short, neat, slightly longer on top than the sides", "maintenance": "Low - wash and go"},
        "textured fringe": {"description": "Fringe with layered texture for movement", "maintenance": "Low - minimal styling"},
        "messy crop": {"description": "Textured crop styled with a deliberately undone look", "maintenance": "Low - minimal styling"},
        "fringe": {"description": "Straight-cut bangs across the forehead", "maintenance": "Medium - regular trims"},
        "caesar cut": {"description": "Short, horizontally-fringed crop", "maintenance": "Low - easy to maintain"},
        # Female styles
        "long layers": {"description": "Long hair cut in layers for movement and volume", "maintenance": "Medium - occasional trims to keep layers fresh"},
        "bob cut": {"description": "Chin-to-shoulder length cut, blunt or lightly layered", "maintenance": "Medium - regular trims to hold shape"},
        "pixie cut": {"description": "Very short, cropped style", "maintenance": "Low - minimal daily styling, frequent trims"},
        "curtain bangs": {"description": "Center-parted bangs swept to both sides framing the face", "maintenance": "Medium - regular trims"},
        "beach waves": {"description": "Loose, tousled waves for a relaxed look", "maintenance": "Low - minimal styling"},
        "side-swept bangs": {"description": "Bangs angled and swept to one side", "maintenance": "Medium - regular trims"},
        "asymmetrical bob": {"description": "Bob with one side cut longer than the other", "maintenance": "Medium - regular trims to keep the asymmetry sharp"},
        "long pixie": {"description": "Pixie cut with slightly longer length on top", "maintenance": "Low - minimal daily styling"},
        "layered lob": {"description": "Shoulder-length cut ('lob') with soft layers", "maintenance": "Medium - occasional trims"},
        "soft layers": {"description": "Gently layered cut for subtle volume and movement", "maintenance": "Low - minimal styling"},
        "long bob": {"description": "Longer bob resting near the collarbone", "maintenance": "Medium - regular trims to hold shape"},
        "wavy lob": {"description": "Shoulder-length cut styled with soft waves", "maintenance": "Low - minimal styling"},
        "chin-length bob": {"description": "Bob cut ending right at the chin", "maintenance": "Medium - regular trims to hold shape"},
        "textured lob": {"description": "Shoulder-length cut with choppy, textured ends", "maintenance": "Low - minimal styling"},
        "textured pixie": {"description": "Pixie cut with piecey, textured layers on top", "maintenance": "Low - minimal daily styling"},
        "blunt bangs": {"description": "Straight-across, full-width bangs", "maintenance": "Medium - regular trims to keep the line crisp"},
        "layered bob": {"description": "Bob cut with internal layers for volume", "maintenance": "Medium - regular trims to hold shape"},
    }

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_path: Optional[str] = None):
        self.config_path = Path(config_path)
        self.model_path = model_path
        self.session = None

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.hair_styles = self.config.get('HAIR_STYLES', {})
        self.face_shapes = self.config.get('FACE_SHAPES', [])

        if model_path:
            self.session = ort.InferenceSession(model_path)
            self.input_name = self.session.get_inputs()[0].name

    def get_styles_for_shape(self, face_shape: str, gender: str) -> List[str]:
        """Get predefined hairstyles for a face shape and gender"""
        return self.hair_styles.get(gender.lower(), {}).get(face_shape.lower(), [])

    def get_style_descriptions(self) -> Dict[str, Dict]:
        """Get detailed descriptions for all hairstyles"""
        return self.STYLE_INFO

    def recommend(
        self,
        face_shape: str,
        gender: Optional[str] = None,
        face_measurements: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> List[HairRecommendation]:
        """
        Recommend hairstyles for a given face shape and gender.

        If gender is omitted, styles for both genders are returned together
        (each tagged with its gender) rather than raising an error.

        Args:
            face_shape: Detected face shape
            gender: "male" or "female"; if None, both are included
            face_measurements: Optional facial measurements for fine-tuning
            user_preferences: Optional user preferences (maintenance, etc.)

        Returns:
            List of HairRecommendation sorted by suitability
        """
        genders = [gender.lower()] if gender else list(self.hair_styles.keys())
        descriptions = self.get_style_descriptions()

        recommendations = []
        for g in genders:
            styles = self.get_styles_for_shape(face_shape, g)
            for style in styles:
                info = descriptions.get(style, {})

                suitability = self._calculate_suitability(
                    style, face_shape, g, face_measurements, user_preferences
                )

                recommendations.append(HairRecommendation(
                    style=style,
                    confidence=suitability,
                    description=info.get("description", ""),
                    maintenance_level=info.get("maintenance", "Unknown"),
                    gender=g,
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
        gender: str,
        measurements: Optional[Dict],
        preferences: Optional[Dict]
    ) -> float:
        """Calculate suitability score for a hairstyle"""
        base_score = 0.7

        # best_for is derived from HAIR_STYLES itself, not duplicated data,
        # so a style always scores highest for the shapes config.yaml lists it under.
        styles_for_shape = self.get_styles_for_shape(face_shape, gender)
        if style in styles_for_shape:
            base_score += 0.2

        if measurements:
            forehead_width = measurements.get('forehead_width', 0)
            face_width = measurements.get('face_width', 0)

            if face_width > 0 and forehead_width / face_width > 0.9:
                if "fringe" in style or "bangs" in style:
                    base_score += 0.1

        if preferences:
            maintenance_pref = preferences.get("maintenance", "medium").lower()
            style_maintenance = self.STYLE_INFO.get(style, {}).get("maintenance", "").lower()

            if maintenance_pref == "low" and "very low" in style_maintenance:
                base_score += 0.1
            elif maintenance_pref == "low" and "low" in style_maintenance:
                base_score += 0.05
            elif maintenance_pref == "high" and "high" in style_maintenance:
                base_score += 0.1

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

    def get_all_styles(self, gender: Optional[str] = None) -> List[str]:
        """Get all available hairstyles, optionally filtered by gender"""
        if gender:
            shapes = self.hair_styles.get(gender.lower(), {})
            styles = set()
            for style_list in shapes.values():
                styles.update(style_list)
            return sorted(styles)
        return list(self.get_style_descriptions().keys())


class HairStyleAnalyzer:
    """High-level hairstyle analysis"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_path: Optional[str] = None):
        self.recommender = HairStyleRecommender(config_path, model_path)
        self.descriptions = self.recommender.get_style_descriptions()

    def analyze(
        self,
        face_shape: str,
        gender: Optional[str] = None,
        measurements: Optional[Dict] = None,
        preferences: Optional[Dict] = None
    ) -> List[HairRecommendation]:
        """Complete hairstyle analysis"""
        return self.recommender.recommend(face_shape, gender, measurements, preferences)

    def get_style_details(self, style: str) -> Dict:
        """Get detailed information about a specific style"""
        return self.descriptions.get(style, {})
