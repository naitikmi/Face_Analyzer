"""
POST /api/visualize - generate a "preview on me" image applying a chosen
beard/hair/glasses style to the user's own submitted photo, via Gemini's
image-editing model.
"""
import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from face_analyzer.services.style_visualizer import (
    StyleVisualizerError,
    StyleVisualizerUnavailable,
    visualizer,
)

router = APIRouter()

_VALID_CATEGORIES = ("beard", "hair", "glasses")


@router.post("/visualize")
async def visualize(
    image: UploadFile = File(...),
    category: str = Form(...),
    style: str = Form(...),
) -> Response:
    if category not in _VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail="category must be 'beard', 'hair', or 'glasses'")
    if not style.strip():
        raise HTTPException(status_code=422, detail="style is required")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    # Fail fast with a clear error rather than sending an unreadable file to Gemini.
    np_arr = np.frombuffer(contents, dtype=np.uint8)
    if cv2.imdecode(np_arr, cv2.IMREAD_COLOR) is None:
        raise HTTPException(status_code=400, detail="Could not decode image - unsupported or corrupt file")

    try:
        preview_bytes = visualizer.generate_preview(contents, category, style)
    except StyleVisualizerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StyleVisualizerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return Response(content=preview_bytes, media_type="image/jpeg")
