"""ResNeXt deepfake detection model implementation.

This module implements a deepfake detection model using ResNeXt architecture.

GitHub: https://github.com/abhijithjadhav/Deepfake_detection_using_deep_learning
"""

import os
from typing import List

import face_recognition
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from ....core.model_hub import download_resnext_model
from ....core.types import DeepfakeDetection
from ..base import BaseDeepfakeDetector


class ResNeXtModel(nn.Module):
    """LSTM-based deepfake detection model using ResNeXt backbone.

    This model processes video sequences by extracting features from individual frames
    using a ResNeXt CNN, then processes the temporal sequence with an LSTM.
    """

    def __init__(
        self,
        num_classes=2,
        latent_dim=2048,
        lstm_layers=1,
        hidden_dim=2048,
        bidirectional=False,
    ):
        """Initialize the model.

        Args:
            num_classes: Number of output classes (2 for real/fake).
            latent_dim: Dimension of CNN feature vectors.
            lstm_layers: Number of LSTM layers.
            hidden_dim: Hidden dimension of LSTM.
            bidirectional: Whether to use bidirectional LSTM.
        """
        super(ResNeXtModel, self).__init__()
        model = models.resnext50_32x4d(pretrained=True)
        self.model = nn.Sequential(*list(model.children())[:-2])
        self.lstm = nn.LSTM(latent_dim, hidden_dim, lstm_layers, bidirectional)
        self.relu = nn.LeakyReLU()
        self.dp = nn.Dropout(0.4)
        self.linear1 = nn.Linear(2048, num_classes)
        self.avgpool = nn.AdaptiveAvgPool2d(1)

    def forward(self, x):
        """Forward pass through the model.

        Args:
            x: Input tensor of shape (batch_size, seq_length, channels, height, width).

        Returns:
            tuple: Feature maps and classification logits.
        """
        batch_size, seq_length, c, h, w = x.shape
        x = x.view(batch_size * seq_length, c, h, w)
        fmap = self.model(x)
        x = self.avgpool(fmap)
        x = x.view(batch_size, seq_length, 2048)
        x_lstm, _ = self.lstm(x, None)
        return fmap, self.dp(self.linear1(x_lstm[:, -1, :]))


class ResNeXtDetector(BaseDeepfakeDetector):
    """ResNeXt deepfake detector implementation.

    A deepfake detection model using ResNeXt architecture with LSTM for temporal
    modeling.

    Attributes:
        device: PyTorch device (CPU/CUDA) for model execution
        model: The ResNeXt-LSTM model for deepfake detection
        confidence_threshold: Minimum confidence for valid detections
        im_size: Input image size for preprocessing
        transform: Image preprocessing transforms
        softmax: Softmax layer for probability conversion
        inv_normalize: Inverse normalization for visualization
    """

    def __init__(
        self,
        model_path: str = None,
        confidence_threshold: float = 0.5,
        device: str = None,
        model_variant: str = "resnext",
        sequence_length: int = 60,
        im_size: int = 112,
    ):
        """Initializes the ResNeXt deepfake detector.

        Args:
            model_path: Path to the trained model checkpoint
            confidence_threshold: Minimum confidence threshold for detections
            device: Device to run inference on ('cpu' or 'cuda'). Auto-detected if None
            model_variant: Model variant. Default is 'resnext'
            sequence_length: Number of frames in sequence for LSTM model
            im_size: Input image size for preprocessing
        """
        super().__init__(confidence_threshold)

        # Set device
        if device is None:
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Model configuration
        self.model_variant = model_variant
        self.sequence_length = sequence_length
        self.im_size = im_size

        # Image preprocessing parameters
        self.mean = [0.485, 0.456, 0.406]
        self.std = [0.229, 0.224, 0.225]

        # Initialize transforms
        self.transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize((self.im_size, self.im_size)),
                transforms.ToTensor(),
                transforms.Normalize(self.mean, self.std),
            ]
        )

        # Inverse normalization for visualization
        self.inv_normalize = transforms.Normalize(
            mean=-1 * np.divide(self.mean, self.std), std=np.divide([1, 1, 1], self.std)
        )

        # Initialize the model
        self.model = self._create_model()

        # Load the trained weights if provided
        if model_path and os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint)
        else:
            try:
                model_path = download_resnext_model()
            except Exception as e:
                raise Exception(f"Failed to download ResNeXt model: {str(e)}")

            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint)

        self.model.to(self.device)
        self.model.eval()

        # Softmax for probability conversion
        self.softmax = nn.Softmax(dim=1)

    def _create_model(self) -> nn.Module:
        """Creates the ResNeXt model architecture.

        Returns:
            ResNeXt model configured for binary classification
        """
        if self.model_variant == "resnext":
            model = ResNeXtModel(num_classes=2)
        else:
            raise ValueError(f"Unsupported model variant: {self.model_variant}")

        return model

    def _extract_face(self, image: np.ndarray) -> np.ndarray:
        """Extract face from image using face_recognition library.

        Args:
            image: Input image as numpy array.

        Returns:
            numpy.ndarray: Cropped face image, or original image if no face found.
        """
        try:
            # Convert PIL to numpy if needed
            if isinstance(image, Image.Image):
                image = np.array(image)

            # Find face locations
            faces = face_recognition.face_locations(image)

            if faces:
                # Use the first detected face
                top, right, bottom, left = faces[0]
                face = image[top:bottom, left:right, :]
                return face
            else:
                print("Warning: No face detected, using full image")
                return image

        except Exception as e:
            print(f"Error in face extraction: {e}")
            return image

    def _create_sequence(self, image: np.ndarray) -> torch.Tensor:
        """Create a sequence from a single image by replicating it.

        Args:
            image: Input image.

        Returns:
            torch.Tensor: Tensor of shape (1, sequence_length, C, H, W).
        """
        # Extract face
        face_image = self._extract_face(image)

        # Apply transforms
        transformed_image = self.transform(face_image)

        # Create sequence by replicating the image
        sequence = torch.stack([transformed_image] * self.sequence_length)

        # Add batch dimension
        sequence = sequence.unsqueeze(0)

        return sequence

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocesses image for model input.

        Args:
            image: Input image as numpy array

        Returns:
            Preprocessed tensor ready for model input
        """
        if self.model_variant == "resnext":
            # Use sequence-based preprocessing for LSTM model
            return self._create_sequence(image)

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
        # Load image
        image = self._load_image(image_path)

        # Preprocess image
        input_tensor = self._preprocess_image(image)

        # Make prediction
        with torch.no_grad():
            fmap, logits = self.model(input_tensor)
            probabilities = self.softmax(logits)
            _, prediction = torch.max(logits, 1)

            deepfake_prob = probabilities[0, 0].item()
            real_prob = probabilities[0, 1].item()

            is_deepfake = deepfake_prob > real_prob
            confidence = max(deepfake_prob, real_prob)

            detection = DeepfakeDetection(
                frame_number=0,  # Single image, so frame 0
                is_deepfake=is_deepfake,
                confidence=confidence,
                model_name=f"{self.model_variant}",
            )

        # Save to CSV if requested
        if save_csv:
            self._save_detections_to_csv(detection, image_path, csv_path)

        return detection, is_deepfake

    def detect_video(
        self,
        video_path: str,
        save_csv: bool = False,
        csv_path: str = "deepfake_detections.csv",
        save_annotated: bool = False,
        output_folder: str = "output",
        num_frames: int = 11,
    ) -> List[DeepfakeDetection]:
        """Detects deepfake in the given video using equally spaced frames.

        Args:
            video_path: Path to the input video
            save_csv: Whether to save detection results to CSV file
            csv_path: Path where to save the CSV file
            save_annotated: Whether to save annotated video with results
            output_folder: Folder path where to save annotated videos
            num_frames: Number of equally spaced frames to analyze (default: 11)

        Returns:
            List of DeepfakeDetection objects for analyzed frames
        """
        # Extract equally spaced frames
        extracted_frames = self._extract_equally_spaced_frames(video_path, num_frames)

        detections = []

        for frame_number, frame in extracted_frames:
            try:
                # Preprocess frame
                input_tensor = self._preprocess_image(frame)

                # Make prediction
                with torch.no_grad():
                    fmap, logits = self.model(input_tensor)
                    probabilities = self.softmax(logits)
                    _, prediction = torch.max(logits, 1)

                    deepfake_prob = probabilities[0, 0].item()
                    real_prob = probabilities[0, 1].item()

                    is_deepfake = deepfake_prob > real_prob
                    confidence = max(deepfake_prob, real_prob)
                    confidence = round(confidence, 2)

                    detection = DeepfakeDetection(
                        frame_number=frame_number,
                        is_deepfake=is_deepfake,
                        confidence=confidence,
                        model_name=f"{self.model_variant}",
                    )

                    detections.append(detection)

            except Exception as e:
                print(f"Skipping frame {frame_number} due to error: {e}")
                continue

        # Aggregate results and print final decision
        if detections:
            final_result, deepfake_count, total_frames = (
                self.aggregate_video_detections(
                    detections, video_path, output_folder, self.model_variant
                )
            )

        # Save annotated video
        if save_annotated and detections:
            self._save_annotated_video(video_path, detections, output_folder)

        # Save to CSV
        if save_csv and detections:
            self._save_detections_to_csv(detections, video_path, csv_path)
            # Save final aggregated result to text file
            self._save_final_video_result_to_txt(
                final_result,
                video_path,
                output_folder,
                self.model_variant,
                deepfake_count,
                total_frames,
            )

        return detections, final_result

    def _tensor_to_image(self, tensor: torch.Tensor) -> np.ndarray:
        """Convert tensor to displayable image.

        Args:
            tensor: Input tensor.

        Returns:
            numpy.ndarray: Image array.
        """
        image = tensor.to("cpu").clone().detach()
        image = image.squeeze()
        image = self.inv_normalize(image)
        image = image.numpy()
        image = image.transpose(1, 2, 0)
        image = image.clip(0, 1)
        return image
