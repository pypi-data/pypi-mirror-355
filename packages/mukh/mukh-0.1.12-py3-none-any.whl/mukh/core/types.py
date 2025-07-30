"""Core type definitions for the mukh package.

This module contains shared data structures and type definitions used across
different modules in the package.
"""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class BoundingBox:
    """Represents a bounding box with coordinates and confidence score.

    Attributes:
        x1: Left x coordinate
        y1: Top y coordinate
        x2: Right x coordinate
        y2: Bottom y coordinate
        confidence: Detection confidence score (0.0 to 1.0)
    """

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1


@dataclass
class FaceDetection:
    """Represents a detected face with bounding box and optional landmarks.

    Attributes:
        bbox: Bounding box coordinates and confidence
        landmarks: Optional array of facial landmark coordinates
    """

    bbox: BoundingBox
    landmarks: Optional[np.ndarray] = None


@dataclass
class DeepfakeDetection:
    """Represents a deepfake detection result.

    Attributes:
        frame_number: Frame number (0 for images, frame index for videos)
        is_deepfake: Whether the content is detected as deepfake
        confidence: Detection confidence score (0.0 to 1.0)
        model_name: Name of the model used for detection
    """

    frame_number: int
    is_deepfake: bool
    confidence: float
    model_name: str
