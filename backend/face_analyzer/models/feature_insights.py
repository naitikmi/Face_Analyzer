"""
Feature Insights Module
Turns geometric measurements and landmark symmetry into a plain-language
breakdown of what's already working in the subject's favor, and where a
style choice can enhance or balance a feature further.

Framing note: this deliberately avoids "good/bad" or "flaw" language.
There's no universal standard for what a face "should" look like - every
feature here is either called out as already flattering, or paired with a
concrete, positive styling tip. Nothing is left as an unadorned criticism.
"""
from dataclasses import dataclass
from typing import Dict, List, Literal

import numpy as np

Verdict = Literal["flattering", "opportunity"]


@dataclass
class FeatureNote:
    """A single feature observation with an actionable styling tip."""
    feature: str
    verdict: Verdict
    observation: str
    tip: str


def _symmetry_offset(landmarks: np.ndarray, left_idx: int, right_idx: int, center_idx: int) -> float:
    """
    How far left/right landmarks deviate from mirror-symmetry around the
    vertical center line, as a fraction of the larger of the two distances.
    0 = perfectly symmetric, larger values = more left-right variation.
    """
    center_x = landmarks[center_idx][0]
    left_dx = abs(landmarks[left_idx][0] - center_x)
    right_dx = abs(landmarks[right_idx][0] - center_x)
    largest = max(left_dx, right_dx)
    if largest == 0:
        return 0.0
    return abs(left_dx - right_dx) / largest


def analyze_features(
    landmarks: np.ndarray,
    ratios: Dict[str, float],
) -> List[FeatureNote]:
    """
    Build a short list of feature-level notes from face-shape ratios and
    raw landmark positions (for symmetry). Mirrors the same rule-based,
    no-training-data approach as FaceShapeClassifier.classify_geometric.
    """
    notes: List[FeatureNote] = []

    # --- Symmetry (landmark indices per MediaPipe Face Mesh topology,
    # matching FaceLandmarkDetector.get_key_landmarks) ---
    jaw_asymmetry = _symmetry_offset(landmarks, 172, 397, 1)
    cheek_asymmetry = _symmetry_offset(landmarks, 116, 345, 1)
    avg_asymmetry = (jaw_asymmetry + cheek_asymmetry) / 2

    if avg_asymmetry < 0.06:
        notes.append(FeatureNote(
            feature="Symmetry",
            verdict="flattering",
            observation="Your jawline and cheekbones sit close to mirror-even side to side.",
            tip="Symmetrical styles - a clean center part, an evenly trimmed beard - play this up.",
        ))
    else:
        notes.append(FeatureNote(
            feature="Symmetry",
            verdict="opportunity",
            observation="There's some natural left-right variation in your jaw and cheekbones - everyone has a bit of this.",
            tip="A side part or slightly asymmetric fringe works with that variation rather than fighting it.",
        ))

    # --- Jawline definition ---
    jaw_ratio = ratios.get("jaw_face_ratio", 0)
    if jaw_ratio >= 0.88:
        notes.append(FeatureNote(
            feature="Jawline",
            verdict="flattering",
            observation="Your jawline is strong and well-defined relative to your face width.",
            tip="Short, clean-lined beard styles like stubble or a boxed beard show it off rather than covering it.",
        ))
    else:
        notes.append(FeatureNote(
            feature="Jawline",
            verdict="opportunity",
            observation="Your jawline is softer and rounder relative to your face width.",
            tip="A structured beard along the jaw, or hair with length at jaw level, adds definition here.",
        ))

    # --- Forehead proportion ---
    forehead_ratio = ratios.get("forehead_face_ratio", 0)
    if 0.85 <= forehead_ratio <= 1.0:
        notes.append(FeatureNote(
            feature="Forehead",
            verdict="flattering",
            observation="Your forehead is well-proportioned to the rest of your face.",
            tip="You have flexibility here - most hairlines and partings will sit well.",
        ))
    elif forehead_ratio > 1.0:
        notes.append(FeatureNote(
            feature="Forehead",
            verdict="opportunity",
            observation="Your forehead reads a little broader relative to your jaw and cheekbones.",
            tip="A fringe or textured bangs bring visual weight down and balance the proportion.",
        ))
    else:
        notes.append(FeatureNote(
            feature="Forehead",
            verdict="opportunity",
            observation="Your forehead reads a little narrower relative to the rest of your face.",
            tip="Swept-back or off-the-face styles - a quiff, a side sweep - open it up and add balance.",
        ))

    # --- Cheekbones ---
    cheekbone_jaw_ratio = ratios.get("cheekbone_jaw_ratio", 0)
    if cheekbone_jaw_ratio >= 1.08:
        notes.append(FeatureNote(
            feature="Cheekbones",
            verdict="flattering",
            observation="Your cheekbones are noticeably more prominent than your jawline - a naturally sculpted feature.",
            tip="Shorter sides with more volume on top draw the eye upward toward them.",
        ))

    # --- Overall face length ---
    height_width_ratio = ratios.get("height_width_ratio", 0)
    if height_width_ratio > 1.55:
        notes.append(FeatureNote(
            feature="Face length",
            verdict="opportunity",
            observation="Your face reads on the longer side relative to its width.",
            tip="Keep height low on top and add width at the sides - a fuller beard, side-swept hair - to balance it.",
        ))
    elif height_width_ratio < 1.1:
        notes.append(FeatureNote(
            feature="Face length",
            verdict="opportunity",
            observation="Your face reads on the shorter, fuller side relative to its width.",
            tip="Added height on top - a quiff or pompadour - elongates the proportions.",
        ))

    return notes
