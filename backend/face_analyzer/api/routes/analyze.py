"""
POST /api/analyze - submit a face image, get back structure analysis and
beard/hair/glasses recommendations.
"""
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from face_analyzer.api.pipeline import AnalysisPipeline
from face_analyzer.api.schemas import AnalyzeResponse

router = APIRouter()

# Constructed once at import time: the underlying MediaPipe/model objects are
# expensive to create, so a single shared pipeline instance serves all
# requests (the pipeline itself holds no per-request state).
pipeline = AnalysisPipeline()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(...),
    gender: Optional[str] = Form(None),
    maintenance_preference: Optional[str] = Form(None),
) -> AnalyzeResponse:
    if gender is not None and gender.lower() not in ("male", "female"):
        raise HTTPException(status_code=422, detail="gender must be 'male' or 'female' if provided")

    if maintenance_preference is not None and maintenance_preference.lower() not in ("low", "medium", "high"):
        raise HTTPException(status_code=422, detail="maintenance_preference must be 'low', 'medium', or 'high'")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    np_arr = np.frombuffer(contents, dtype=np.uint8)
    decoded = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="Could not decode image - unsupported or corrupt file")

    # decoded is processed entirely in memory and discarded once this
    # function returns - no image data is ever written to disk.
    result = pipeline.analyze(
        decoded,
        gender=gender.lower() if gender else None,
        maintenance_preference=maintenance_preference.lower() if maintenance_preference else None,
    )
    return result
