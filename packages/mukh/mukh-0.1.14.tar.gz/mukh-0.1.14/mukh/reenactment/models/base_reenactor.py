"""Base class defining the interface for face reenactment implementations.

This module provides the abstract base class that all face reenactment implementations
must inherit from, ensuring a consistent interface across different models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import numpy as np


class BaseFaceReenactor(ABC):
    """Abstract base class for face reenactment implementations.

    All face reenactment implementations must inherit from this class and implement
    the required abstract methods.

    Attributes:
        model_path: Path to the model weights/checkpoints.
        device: Device to run inference on ('cpu', 'cuda', etc.).
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """Initializes the face reenactor.

        Args:
            model_path: Path to the model weights or checkpoint file.
            device: Device to run inference on ('cpu', 'cuda', etc.).
                Defaults to 'cpu'.
        """
        self.model_path = model_path
        self.device = device

    @abstractmethod
    def _load_model(self) -> None:
        """Loads the reenactment model from the specified path.

        Implementations should handle loading the model architecture and weights,
        and placing the model on the specified device.

        Raises:
            ValueError: If the model cannot be loaded from the given path.
        """
        pass

    @abstractmethod
    def reenact_from_video(
        self,
        source_path: str,
        driving_video_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """Performs face reenactment using a source image and driving video.

        Args:
            source_path: Path to the source image (face to be animated).
            driving_video_path: Path to the driving video (facial motion to transfer).
            output_path: Optional path to save the output video. If None, a default
                path will be used.

        Returns:
            str: Path to the generated output video.
        """
        pass
