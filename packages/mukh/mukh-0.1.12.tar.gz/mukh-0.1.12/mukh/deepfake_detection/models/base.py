"""Base class defining the interface for deepfake detection implementations.

This module provides the abstract base class that all deepfake detector implementations
must inherit from, ensuring a consistent interface across different models.
"""

import csv
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np

from ...core.types import DeepfakeDetection


class BaseDeepfakeDetector(ABC):
    """Abstract base class for deepfake detector implementations.

    All deepfake detector implementations must inherit from this class and implement
    the required abstract methods.

    Attributes:
        confidence_threshold: Float threshold (0-1) for detection confidence.
    """

    def __init__(self, confidence_threshold: float = 0.5):
        """Initializes the deepfake detector.

        Args:
            confidence_threshold: Minimum confidence threshold for detections.
                Defaults to 0.5.
        """
        self.confidence_threshold = confidence_threshold

    def _load_image(self, image_path: str) -> np.ndarray:
        """Loads an image from disk in BGR format.

        Args:
            image_path: Path to the image file.

        Returns:
            np.ndarray: The loaded image in BGR format.

        Raises:
            ValueError: If the image cannot be loaded from the given path.
        """
        if not os.path.exists(image_path):
            raise ValueError(f"Image path does not exist: {image_path}")

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from: {image_path}")

        return image

    def _load_video(self, video_path: str) -> cv2.VideoCapture:
        """Loads a video from disk.

        Args:
            video_path: Path to the video file.

        Returns:
            cv2.VideoCapture: The loaded video capture object.

        Raises:
            ValueError: If the video cannot be loaded from the given path.
        """
        if not os.path.exists(video_path):
            raise ValueError(f"Video path does not exist: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not load video from: {video_path}")

        return cap

    @abstractmethod
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
            image_path: Path to the input image.
            save_csv: Whether to save detection results to CSV file.
            csv_path: Path where to save the CSV file.
            save_annotated: Whether to save annotated image with results.
            output_folder: Folder path where to save annotated images.

        Returns:
            DeepfakeDetection object containing detection results.
        """
        pass

    @abstractmethod
    def detect_video(
        self,
        video_path: str,
        save_csv: bool = False,
        csv_path: str = "deepfake_detections.csv",
        save_annotated: bool = False,
        output_folder: str = "output",
        frame_interval: int = 30,
    ) -> List[DeepfakeDetection]:
        """Detects deepfake in the given video.

        Args:
            video_path: Path to the input video.
            save_csv: Whether to save detection results to CSV file.
            csv_path: Path where to save the CSV file.
            save_annotated: Whether to save annotated video with results.
            output_folder: Folder path where to save annotated videos.
            frame_interval: Interval between frames to analyze (default: 30).

        Returns:
            List of DeepfakeDetection objects for analyzed frames.
        """
        pass

    def detect(
        self,
        media_path: str,
        save_csv: bool = False,
        csv_path: str = "deepfake_detections.csv",
        save_annotated: bool = False,
        output_folder: str = "output",
        frame_interval: int = 30,
    ) -> Union[DeepfakeDetection, List[DeepfakeDetection]]:
        """Detects deepfake in the given image or video.

        Args:
            media_path: Path to the input image or video.
            save_csv: Whether to save detection results to CSV file.
            csv_path: Path where to save the CSV file.
            save_annotated: Whether to save annotated media with results.
            output_folder: Folder path where to save annotated media.
            frame_interval: Interval between frames to analyze for videos.

        Returns:
            DeepfakeDetection for images or List[DeepfakeDetection] for videos.

        Raises:
            ValueError: If the media file format is not supported.
        """
        # Determine if input is image or video based on file extension
        _, ext = os.path.splitext(media_path.lower())

        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

        if ext in image_extensions:
            return self.detect_image(
                media_path, save_csv, csv_path, save_annotated, output_folder
            )
        elif ext in video_extensions:
            return self.detect_video(
                media_path,
                save_csv,
                csv_path,
                save_annotated,
                output_folder,
                frame_interval,
            )
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _save_detections_to_csv(
        self,
        detections: Union[DeepfakeDetection, List[DeepfakeDetection]],
        media_path: str,
        csv_path: str,
    ) -> None:
        """Saves deepfake detection results to a CSV file.

        Args:
            detections: Single detection or list of detections to save.
            media_path: Path to the source media file.
            csv_path: Path where to save the CSV file.
        """
        # Extract just the filename from the full path
        media_name = os.path.basename(media_path)

        # Ensure detections is a list
        if isinstance(detections, DeepfakeDetection):
            detections = [detections]

        # Check if CSV file exists to determine if we need to write headers
        file_exists = os.path.exists(csv_path)

        # Create directory if it doesn't exist
        os.makedirs(
            os.path.dirname(csv_path) if os.path.dirname(csv_path) else ".",
            exist_ok=True,
        )

        # Open CSV file in append mode
        with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "media_name",
                "frame_number",
                "is_deepfake",
                "confidence",
                "model_name",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header if file is new
            if not file_exists:
                writer.writeheader()

            # Write detection results
            for detection in detections:
                writer.writerow(
                    {
                        "media_name": media_name,
                        "frame_number": detection.frame_number,
                        "is_deepfake": detection.is_deepfake,
                        "confidence": detection.confidence,
                        "model_name": detection.model_name,
                    }
                )

    def _annotate_image(
        self, image: np.ndarray, detection: DeepfakeDetection
    ) -> np.ndarray:
        """Annotates image with deepfake detection results.

        Args:
            image: Input image as numpy array.
            detection: Deepfake detection result.

        Returns:
            np.ndarray: Copy of input image with detection results annotated.
        """
        image_copy = image.copy()

        # Choose color based on detection result
        color = (
            (0, 0, 255) if detection.is_deepfake else (0, 255, 0)
        )  # Red for deepfake, green for real

        # Add detection result text
        label = f"{'DEEPFAKE' if detection.is_deepfake else 'REAL'}: {detection.confidence:.2f}"

        # Add background rectangle for text
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        cv2.rectangle(
            image_copy, (10, 10), (20 + text_size[0], 40 + text_size[1]), color, -1
        )

        # Add text
        cv2.putText(
            image_copy,
            label,
            (15, 35 + text_size[1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
        )

        return image_copy

    def _save_annotated_image(
        self,
        image: np.ndarray,
        detection: DeepfakeDetection,
        image_path: str,
        output_folder: str,
    ) -> str:
        """Saves annotated image with deepfake detection results.

        Args:
            image: Original image.
            detection: Deepfake detection result.
            image_path: Path to the original image.
            output_folder: Folder where to save the annotated image.

        Returns:
            str: Path to the saved annotated image.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Annotate image
        annotated_image = self._annotate_image(image, detection)

        # Create output filename
        image_name = os.path.basename(image_path)
        name, ext = os.path.splitext(image_name)
        output_filename = f"{name}_deepfake_detected{ext}"
        output_path = os.path.join(output_folder, output_filename)

        # Save annotated image
        cv2.imwrite(output_path, annotated_image)

        return output_path

    def _save_annotated_video(
        self,
        video_path: str,
        detections: List[DeepfakeDetection],
        output_folder: str,
    ) -> str:
        """Saves annotated video with deepfake detection results.

        Args:
            video_path: Path to the original video.
            detections: List of deepfake detection results.
            output_folder: Folder where to save the annotated video.

        Returns:
            str: Path to the saved annotated video.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Create output filename
        video_name = os.path.basename(video_path)
        name, ext = os.path.splitext(video_name)
        output_filename = f"{name}_deepfake_detected{ext}"
        output_path = os.path.join(output_folder, output_filename)

        # Open input video
        cap = cv2.VideoCapture(video_path)

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Create detection lookup for quick access
        detection_dict = {det.frame_number: det for det in detections}

        frame_number = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Annotate frame if we have detection for it
            if frame_number in detection_dict:
                frame = self._annotate_image(frame, detection_dict[frame_number])

            out.write(frame)
            frame_number += 1

        # Release everything
        cap.release()
        out.release()

        return output_path

    def _extract_equally_spaced_frames(
        self, video_path: str, num_frames: int = 11
    ) -> List[Tuple[int, np.ndarray]]:
        """Extracts equally spaced frames from a video.

        Args:
            video_path: Path to the video file.
            num_frames: Number of frames to extract (default: 11).

        Returns:
            List of tuples containing (frame_number, frame_array) for extracted frames.

        Raises:
            ValueError: If the video cannot be loaded or has insufficient frames.
        """
        cap = self._load_video(video_path)

        # Get total number of frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames < num_frames:
            cap.release()
            raise ValueError(
                f"Video has only {total_frames} frames, cannot extract {num_frames} frames"
            )

        # Calculate frame indices to extract
        if num_frames == 1:
            frame_indices = [total_frames // 2]  # Middle frame
        else:
            # Equally space frames across the video
            frame_indices = [
                int(i * (total_frames - 1) / (num_frames - 1))
                for i in range(num_frames)
            ]

        extracted_frames = []

        for frame_idx in frame_indices:
            # Set video position to the desired frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if ret:
                extracted_frames.append((frame_idx, frame))
            else:
                # If we can't read the frame, skip it
                continue

        cap.release()

        if not extracted_frames:
            raise ValueError("Could not extract any frames from the video")

        return extracted_frames

    def aggregate_video_detections(
        self,
        detections: List[DeepfakeDetection],
        video_path: str,
        output_folder: str,
        model_name: str,
    ) -> bool:
        """Aggregates video detections to determine final result.

        Args:
            detections: List of DeepfakeDetection objects from video frames
            video_path: Path to the video file for logging purposes
            output_folder: Folder path where to save the text file
            model_name: Name of the model for display purposes

        Returns:
            bool: True if video is classified as deepfake, False otherwise,
            int: Number of frames detected as deepfake
            int: Total number of frames analyzed
        """
        if not detections:
            print(f"No detections found for video: {video_path}")
            return False

        # Count deepfake detections
        deepfake_count = sum(1 for detection in detections if detection.is_deepfake)
        total_frames = len(detections)

        # Determine final result based on majority voting
        is_final_deepfake = deepfake_count >= (total_frames / 2)

        # Print results
        print(f"\n=== Video Analysis Results ===")
        print(f"Video: {video_path}")
        print(f"Total frames analyzed: {total_frames}")
        print(f"Frames detected as deepfake: {deepfake_count}")
        print(f"Frames detected as real: {total_frames - deepfake_count}")
        print(f"Final classification: {'DEEPFAKE' if is_final_deepfake else 'REAL'}")
        print(f"Model: {model_name}")
        print("=" * 30)

        return is_final_deepfake, deepfake_count, total_frames

    def _save_final_video_result_to_txt(
        self,
        is_final_deepfake: bool,
        video_path: str,
        output_folder: str,
        model_name: str,
        deepfake_count: int,
        total_frames: int,
    ) -> None:
        """Saves the final aggregated video result to a text file.

        Args:
            is_final_deepfake: Final aggregated decision for the video
            video_path: Path to the video file
            output_folder: Folder path where to save the text file
            model_name: Name of the model for display purposes
            deepfake_count: Number of frames detected as deepfake
            total_frames: Total number of frames analyzed
        """

        # Create text file path based on output folder
        txt_filename = "video_final_results.txt"
        txt_path = os.path.join(output_folder, txt_filename)

        # Create directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Extract just the filename from the full path
        media_name = os.path.basename(video_path)

        # Append to text file
        with open(txt_path, "a", encoding="utf-8") as txtfile:
            txtfile.write(
                f" | {media_name} | {model_name} | {deepfake_count}/{total_frames} deepfake frames | Final: {'DEEPFAKE' if is_final_deepfake else 'REAL'}\n"
            )

        print(f"Final result saved to: {txt_path}")
