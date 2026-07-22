"""
Pydantic request/response schemas for the Face Analyzer API.
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel


class FaceShapeInfo(BaseModel):
    shape: str
    confidence: float
    description: str
    all_scores: Dict[str, float]
    measurements: Dict[str, float]


class RecommendationItem(BaseModel):
    style: str
    style_slug: str
    suitability_score: float
    description: str
    image_url: str


class HairRecommendationItem(RecommendationItem):
    gender: str


class RecommendationSet(BaseModel):
    beard: List[RecommendationItem]
    hair: List[HairRecommendationItem]
    glasses: List[RecommendationItem]


class FeatureInsight(BaseModel):
    feature: str
    verdict: Literal["flattering", "opportunity"]
    observation: str
    tip: str


class ExtensionsInfo(BaseModel):
    # Placeholders for Phase 2 features (skin/acne analysis, feedback-driven
    # offline retraining). Populated once those features ship; left null so
    # the response shape doesn't need to change when they do.
    skin_analysis: Optional[dict] = None
    feedback_submission_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    face_detected: bool
    face_count: int
    face_shape: Optional[FaceShapeInfo] = None
    recommendations: Optional[RecommendationSet] = None
    feature_insights: Optional[List[FeatureInsight]] = None
    extensions: ExtensionsInfo
