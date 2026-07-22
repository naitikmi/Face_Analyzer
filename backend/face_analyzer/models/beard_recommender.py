"""
Beard Style Recommender Module
Recommends beard styles based on face shape
"""
import yaml
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import onnxruntime as ort


DEFAULT_CONFIG_PATH = str(Path(__file__).resolve().parents[2] / "config.yaml")


@dataclass
class BeardRecommendation:
    """Beard style recommendation result"""
    style: str
    confidence: float
    description: str
    maintenance_level: str
    suitability_score: float


class BeardStyleRecommender:
    """Recommends beard styles based on face shape and facial features"""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_path: Optional[str] = None):
        self.config_path = Path(config_path)
        self.model_path = model_path
        self.session = None
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.beard_styles = self.config.get('BEARD_STYLES', {})
        self.face_shapes = self.config.get('FACE_SHAPES', [])
        
        if model_path:
            self.session = ort.InferenceSession(model_path)
            self.input_name = self.session.get_inputs()[0].name
    
    def get_styles_for_shape(self, face_shape: str) -> List[str]:
        """Get predefined beard styles for a face shape"""
        return self.beard_styles.get(face_shape.lower(), [])
    
    def get_style_descriptions(self) -> Dict[str, Dict]:
        """Get detailed descriptions for all beard styles"""
        return {
            "full beard": {
                "description": "Classic full beard covering cheeks, jawline, and chin",
                "maintenance": "Medium - regular trimming and shaping needed",
                "best_for": ["oval", "square", "diamond", "oblong", "triangle"]
            },
            "goatee": {
                "description": "Hair on chin only, sometimes with mustache",
                "maintenance": "Low - minimal trimming required",
                "best_for": ["oval", "round", "square", "heart", "diamond", "triangle"]
            },
            "stubble": {
                "description": "Short facial hair (1-3mm) for rugged look",
                "maintenance": "Very Low - occasional trimming",
                "best_for": ["oval", "square", "heart", "diamond", "oblong", "triangle"]
            },
            "van dyke": {
                "description": "Goatee with disconnected mustache",
                "maintenance": "Medium - precise shaping needed",
                "best_for": ["oval", "round", "heart", "diamond", "triangle"]
            },
            "anchor beard": {
                "description": "Pointed beard along jawline with soul patch",
                "maintenance": "High - requires precise trimming",
                "best_for": ["oval", "diamond"]
            },
            "extended goatee": {
                "description": "Goatee extended along jawline",
                "maintenance": "Medium - regular shaping",
                "best_for": ["round"]
            },
            "chin strap": {
                "description": "Thin line of hair along jawline connecting to chin",
                "maintenance": "High - very precise trimming",
                "best_for": ["round", "heart", "diamond", "triangle"]
            },
            "soul patch": {
                "description": "Small patch of hair below lower lip",
                "maintenance": "Very Low - minimal maintenance",
                "best_for": ["round", "heart"]
            },
            "balbo": {
                "description": "Trimmed beard with disconnected mustache and soul patch",
                "maintenance": "Medium - regular shaping",
                "best_for": ["round"]
            },
            "circle beard": {
                "description": "Goatee and mustache connected in circle",
                "maintenance": "Medium - precise shaping",
                "best_for": ["square"]
            },
            "chin curtain": {
                "description": "Hair along jawline and chin, no mustache",
                "maintenance": "Low - occasional trimming",
                "best_for": ["square", "oblong"]
            },
            "mutton chops": {
                "description": "Sideburns extended to jawline, chin clean",
                "maintenance": "Medium - regular trimming",
                "best_for": ["square", "oblong"]
            },
            "garibaldi": {
                "description": "Wide, full beard with rounded bottom",
                "maintenance": "Medium - regular trimming",
                "best_for": ["oblong"]
            }
        }
    
    def recommend(
        self,
        face_shape: str,
        face_measurements: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> List[BeardRecommendation]:
        """
        Recommend beard styles for given face shape
        
        Args:
            face_shape: Detected face shape
            face_measurements: Optional facial measurements for fine-tuning
            user_preferences: Optional user preferences (maintenance, length, etc.)
            
        Returns:
            List of BeardRecommendation sorted by suitability
        """
        styles = self.get_styles_for_shape(face_shape)
        descriptions = self.get_style_descriptions()
        
        recommendations = []
        for style in styles:
            desc = descriptions.get(style, {})
            
            suitability = self._calculate_suitability(
                style, face_shape, face_measurements, user_preferences
            )
            
            recommendations.append(BeardRecommendation(
                style=style,
                confidence=suitability,
                description=desc.get("description", ""),
                maintenance_level=desc.get("maintenance", "Unknown"),
                suitability_score=suitability
            ))
        
        if self.session is not None and face_measurements:
            ml_scores = self._ml_predict(face_shape, face_measurements)
            for i, rec in enumerate(recommendations):
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
        """Calculate suitability score for a beard style"""
        base_score = 0.7
        
        descriptions = self.get_style_descriptions()
        style_info = descriptions.get(style, {})
        best_for = style_info.get("best_for", [])
        
        if face_shape.lower() in best_for:
            base_score += 0.2
        
        if measurements:
            jaw_width = measurements.get('jaw_width', 0)
            face_width = measurements.get('face_width', 0)
            chin_to_mouth = measurements.get('chin_to_mouth', 0)
            
            if "circle beard" in style or "chin strap" in style:
                if jaw_width / face_width > 0.85:
                    base_score += 0.1
            
            if "goatee" in style or "van dyke" in style:
                if chin_to_mouth > 0:
                    base_score += 0.05
        
        if preferences:
            maintenance_pref = preferences.get("maintenance", "medium").lower()
            style_maintenance = style_info.get("maintenance", "").lower()
            
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
            measurements.get('chin_to_mouth', 0),
            measurements.get('mouth_width', 0),
        ], dtype=np.float32)
        
        return np.concatenate([shape_encoding, measurement_features])
    
    def get_all_styles(self) -> List[str]:
        """Get all available beard styles"""
        return list(self.get_style_descriptions().keys())


class BeardStyleAnalyzer:
    """High-level beard style analysis"""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, model_path: Optional[str] = None):
        self.recommender = BeardStyleRecommender(config_path, model_path)
        self.descriptions = self.recommender.get_style_descriptions()
    
    def analyze(
        self,
        face_shape: str,
        measurements: Optional[Dict] = None,
        preferences: Optional[Dict] = None
    ) -> List[BeardRecommendation]:
        """Complete beard style analysis"""
        return self.recommender.recommend(face_shape, measurements, preferences)
    
    def get_style_details(self, style: str) -> Dict:
        """Get detailed information about a specific style"""
        return self.descriptions.get(style, {})