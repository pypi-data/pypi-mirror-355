"""Face reenactment module providing a unified interface for multiple reenactment models.

This module provides a factory class for creating face reenactors with different
underlying implementations. It supports multiple reenactment models through a consistent
interface.

Example:
    Basic usage with default settings:

    >>> from mukh.reenactment import FaceReenactor
    >>> reenactor = FaceReenactor.create("tps")
    >>> result = reenactor.reenact("source.jpg", "driving.jpg")

    For video reenactment:

    >>> result_path = reenactor.reenact_from_video("source.jpg", "driving.mp4")
"""

import os
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np

from ..core.model_hub import download_reenactment_config, download_reenactment_model
from .models.base_reenactor import BaseFaceReenactor
from .models.thin_plate_spline.tps_reenactor import ThinPlateSplineReenactor

ReenactorType = Literal["tps"]


class FaceReenactor:
    """Factory class for creating face reenactment model instances.

    This class provides a unified interface to create and use different face reenactment
    models through a consistent API.
    """

    @staticmethod
    def create(
        model: ReenactorType,
        model_path: Optional[str] = None,
        config_path: Optional[str] = None,
        model_name: str = "vox",
        device: str = "cpu",
        **kwargs,
    ) -> BaseFaceReenactor:
        """Creates a face reenactor instance of the specified type.

        Args:
            model: The type of reenactor to create. Currently supports: "tps"
                (Thin Plate Spline).
            model_path: Path to the model weights. If None, downloads from Hugging Face.
            config_path: Path to the config file. If None, downloads from Hugging Face.
            model_name: Name of the model to download ("vox", "ted", "taichi", "mgif").
                Defaults to "vox".
            device: Device to run inference on ('cpu', 'cuda'). Defaults to 'cpu'.
            **kwargs: Additional model-specific parameters.

        Returns:
            A BaseFaceReenactor instance of the requested type.

        Raises:
            ValueError: If the specified model type is not supported.
        """
        # Define available models and their configurations
        available_models = ["tps"]

        if model not in available_models:
            raise ValueError(
                f"Unknown reenactor model: {model}. "
                f"Available models: {available_models}"
            )

        # Download model checkpoint from Hugging Face if not provided
        if model_path is None:
            try:
                model_path = download_reenactment_model(model_name)
            except Exception as e:
                raise Exception(f"Failed to download reenactment model: {str(e)}")

        # Download config file from Hugging Face if not provided
        if config_path is None:
            try:
                config_path = download_reenactment_config(model_name)
            except Exception as e:
                raise Exception(f"Failed to download reenactment config: {str(e)}")

        # Create the reenactor instance
        if model == "tps":
            return ThinPlateSplineReenactor(
                model_path=model_path,
                config_path=config_path,
                device=device,
                **kwargs,
            )

        # This should never be reached due to the check above
        raise ValueError(f"Model {model} is not implemented yet")

    @staticmethod
    def list_available_models() -> List[str]:
        """Returns a list of available face reenactment model names.

        Returns:
            List of strings containing supported model names.
        """
        return ["tps"]
