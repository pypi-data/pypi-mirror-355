"""Unified deepfake detection interface.

This module provides a unified interface for deepfake detection across
different model implementations. It follows the same pattern as the
face detection module for consistency.
"""

import os
from typing import List, Union

from ..core.types import DeepfakeDetection
from .models.efficientnet.efficientnet_detector import EfficientNetDetector
from .models.resnet_inception.resnet_inception_detector import ResNetInceptionDetector
from .models.resnext.resnext_detector import ResNeXtDetector


class DeepfakeDetector:
    """Unified deepfake detector interface.

    Provides a consistent API for deepfake detection using different
    underlying models. Currently supports ResNet Inception, ResNeXt, and EfficientNet models.

    Attributes:
        model_name: Name of the detection model being used
        detector: The underlying detection model instance
        confidence_threshold: Minimum confidence for valid detections
    """

    def __init__(
        self,
        model_name: str = "resnet_inception",
        model_path: str = None,
        confidence_threshold: float = 0.5,
        device: str = None,
        **kwargs,
    ):
        """Initializes the deepfake detector.

        Args:
            model_name: Name of the model to use ('resnet_inception', 'resnext', 'efficientnet')
            model_path: Optional custom path to model weights file
            confidence_threshold: Minimum confidence threshold for detections
            device: Device to run inference on ('cpu' or 'cuda'). Auto-detected if None
            **kwargs: Additional arguments passed to the specific detector

        Raises:
            ValueError: If an unsupported model name is provided
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold

        if model_name == "resnet_inception":
            self.detector = ResNetInceptionDetector(
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device,
            )
        elif model_name == "resnext":
            self.detector = ResNeXtDetector(
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device,
                **kwargs,
            )
        elif model_name == "efficientnet":
            self.detector = EfficientNetDetector(
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")

    def detect_image(
        self,
        image_path: str,
        save_csv: bool = False,
        csv_path: str = "deepfake_detections.csv",
        save_annotated: bool = False,
        output_folder: str = "output",
    ) -> DeepfakeDetection:
        """Detects deepfake in the given image.

        Args:
            image_path: Path to the input image
            save_csv: Whether to save detection results to CSV file
            csv_path: Path where to save the CSV file
            save_annotated: Whether to save annotated image with results
            output_folder: Folder path where to save annotated images

        Returns:
            DeepfakeDetection object containing detection results
        """
        return self.detector.detect_image(
            image_path=image_path,
            save_csv=save_csv,
            csv_path=csv_path,
            save_annotated=save_annotated,
            output_folder=output_folder,
        )

    def detect_video(
        self,
        video_path: str,
        save_csv: bool = False,
        csv_path: str = "deepfake_detections.csv",
        save_annotated: bool = False,
        output_folder: str = "output",
        num_frames: int = 11,
    ) -> List[DeepfakeDetection]:
        """Detects deepfake in the given video.

        Args:
            video_path: Path to the input video
            save_csv: Whether to save detection results to CSV file
            csv_path: Path where to save the CSV file
            save_annotated: Whether to save annotated video with results
            output_folder: Folder path where to save annotated videos
            num_frames: Number of equally spaced frames to analyze

        Returns:
            List of DeepfakeDetection objects for analyzed frames
        """
        return self.detector.detect_video(
            video_path=video_path,
            save_csv=save_csv,
            csv_path=csv_path,
            save_annotated=save_annotated,
            output_folder=output_folder,
            num_frames=num_frames,
        )

    def detect(
        self,
        media_path: str,
        save_csv: bool = False,
        csv_path: str = "deepfake_detections.csv",
        save_annotated: bool = False,
        output_folder: str = "output",
        num_frames: int = 11,
    ) -> Union[DeepfakeDetection, List[DeepfakeDetection]]:
        """Detects deepfake in the given media file (image or video).

        Automatically determines whether the input is an image or video
        based on file extension and calls the appropriate detection method.

        Args:
            media_path: Path to the input media file (image or video)
            save_csv: Whether to save detection results to CSV file
            csv_path: Path where to save the CSV file
            save_annotated: Whether to save annotated media with results
            output_folder: Folder path where to save annotated media
            num_frames: Number of equally spaced frames to analyze for videos (default: 11)

        Returns:
            DeepfakeDetection for images, List[DeepfakeDetection] for videos

        Raises:
            ValueError: If the file format is not supported
            FileNotFoundError: If the media file doesn't exist
        """
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Media file not found: {media_path}")

        # Get file extension
        _, ext = os.path.splitext(media_path.lower())

        # Image extensions
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
        # Video extensions
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

        if ext in image_extensions:
            return self.detect_image(
                image_path=media_path,
                save_csv=save_csv,
                csv_path=csv_path,
                save_annotated=save_annotated,
                output_folder=output_folder,
            )
        elif ext in video_extensions:
            return self.detect_video(
                video_path=media_path,
                save_csv=save_csv,
                csv_path=csv_path,
                save_annotated=save_annotated,
                output_folder=output_folder,
                num_frames=num_frames,
            )
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def get_model_info(self) -> dict:
        """Returns information about the current model.

        Returns:
            Dictionary containing model information including name,
            confidence threshold, and device.
        """
        return {
            "model_name": self.model_name,
            "confidence_threshold": self.confidence_threshold,
            "device": (
                str(self.detector.device)
                if hasattr(self.detector, "device")
                else "unknown"
            ),
        }

    def set_confidence_threshold(self, threshold: float) -> None:
        """Updates the confidence threshold for detections.

        Args:
            threshold: New confidence threshold (0.0 to 1.0)

        Raises:
            ValueError: If threshold is not between 0.0 and 1.0
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")

        self.confidence_threshold = threshold
        self.detector.confidence_threshold = threshold
