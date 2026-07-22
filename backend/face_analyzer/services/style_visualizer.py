"""
Style Visualizer Service
Generates a "preview on me" image by editing the user's own submitted
photo with Gemini's image-editing model - applying a specific beard,
hairstyle, or glasses style while preserving the person's identity,
face, and photo background.

Requires GEMINI_API_KEY to be set (see backend/.env.example). This is
intentionally isolated from the rest of the pipeline: everything else in
the app works with no API key at all, and this module only raises when
someone actually tries to use it without one configured.
"""
import io
import os
from typing import Literal

from google import genai
from google.genai import errors as genai_errors
from PIL import Image

StyleCategory = Literal["beard", "hair", "glasses"]

MODEL_NAME = "gemini-2.5-flash-image"

_CATEGORY_INSTRUCTIONS = {
    "beard": "give the person a \"{style}\" beard",
    "hair": "give the person a \"{style}\" hairstyle",
    "glasses": "put \"{style}\" glasses on the person",
}


class StyleVisualizerUnavailable(RuntimeError):
    """Raised when GEMINI_API_KEY isn't configured."""


class StyleVisualizerError(RuntimeError):
    """Raised when the Gemini call fails or returns no image."""


def _build_prompt(category: StyleCategory, style: str) -> str:
    change = _CATEGORY_INSTRUCTIONS[category].format(style=style)
    return (
        f"Edit this photo realistically: {change}. "
        "Keep the person's face, identity, skin tone, expression, pose, "
        "and the photo's background and lighting exactly as they are - "
        "change only what's described above. "
        "The result must look like a natural, photorealistic photograph, "
        "not an illustration or painting."
    )


class StyleVisualizer:
    def __init__(self):
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is not None:
            return self._client

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise StyleVisualizerUnavailable(
                "GEMINI_API_KEY is not set - the 'preview on me' feature isn't configured. "
                "See backend/.env.example."
            )
        self._client = genai.Client(api_key=api_key)
        return self._client

    def generate_preview(self, image_bytes: bytes, category: StyleCategory, style: str) -> bytes:
        """
        Edit the given photo to show the person wearing/styled with the
        given category+style. Returns JPEG bytes.
        """
        client = self._get_client()
        source_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        prompt = _build_prompt(category, style)

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[source_image, prompt],
            )
        except genai_errors.APIError as exc:
            if exc.code == 429:
                raise StyleVisualizerError(
                    "Gemini's image model is rate-limited or out of quota for this API key. "
                    "Image generation isn't included in the free tier - check billing at "
                    "https://aistudio.google.com/apikey for the project this key belongs to."
                ) from exc
            raise StyleVisualizerError(f"Gemini request failed ({exc.code}): {exc.message}") from exc

        candidates = response.candidates or []
        for candidate in candidates:
            if not candidate.content or not candidate.content.parts:
                continue
            for part in candidate.content.parts:
                if part.inline_data is not None:
                    result_image = part.as_image()
                    buffer = io.BytesIO()
                    result_image.convert("RGB").save(buffer, format="JPEG", quality=90)
                    return buffer.getvalue()

        raise StyleVisualizerError("Gemini didn't return an image for this request.")


visualizer = StyleVisualizer()
