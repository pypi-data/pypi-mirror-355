"""
V2 Ensemble Deepfake Detection Pipeline

This pipeline runs multiple deepfake detection models and performs weighted averaging
of their results to produce a final ensemble prediction.

Usage:
from mukh.pipelines.deepfake_detection import PipelineDeepfakeDetection

model_configs = {"resnet_inception": 0.5, "efficientnet": 0.5}
detector = PipelineDeepfakeDetection(model_configs)
result = detector.detect("path/to/media", "path/to/output")
"""

import argparse
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
import torch

from mukh.deepfake_detection import DeepfakeDetector


class PipelineDeepfakeDetection:
    """Deepfake detection pipeline that combines multiple models with weighted averaging.

    This class runs multiple deepfake detection models and performs weighted averaging
    of their results to produce a final ensemble prediction.

    Attributes:
        model_configs: Dictionary mapping model names to their weights
        device: PyTorch device for model execution
        confidence_threshold: Threshold for ensemble prediction
    """

    def __init__(
        self,
        model_configs: Dict[str, float],
        device: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ):
        """Initialize the ensemble deepfake detector.

        Args:
            model_configs: Dictionary mapping model names to their weights
                          e.g., {"resnet_inception": 0.5, "efficientnet": 0.5}
            device: Device to run inference on ('cpu' or 'cuda'). Auto-detected if None
            confidence_threshold: Threshold for ensemble prediction (default: 0.5)
        """
        self.model_configs = model_configs
        self.confidence_threshold = confidence_threshold

        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Validate model configurations
        self._validate_model_configs()

    def _validate_model_configs(self) -> None:
        """Validate model configurations.

        Raises:
            ValueError: If model configurations are invalid
        """
        if not self.model_configs:
            raise ValueError("Model configurations cannot be empty")

        valid_models = {"resnet_inception", "efficientnet"}
        for model_name in self.model_configs.keys():
            if model_name not in valid_models:
                raise ValueError(
                    f"Invalid model name: {model_name}. Valid models: {valid_models}"
                )

        # Check if weights sum to a reasonable value
        total_weight = sum(self.model_configs.values())
        if total_weight <= 0:
            raise ValueError("Total weight must be positive")

    def _run_individual_models(
        self,
        media_path: str,
        output_folder: str,
        save_csv: bool = True,
        num_frames: int = 11,
    ) -> Tuple[List[pd.DataFrame], bool]:
        """Run individual deepfake detection models.

        Args:
            media_path: Path to the media file (image or video) to analyze
            output_folder: Folder path to save all outputs
            save_csv: Whether to save individual model results to CSV
            num_frames: Number of equally spaced frames for video analysis

        Returns:
            Tuple of (list of detection dataframes, success flag)
        """
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        detection_dataframes = []

        # Run each model and save results
        for model_name, weight in self.model_configs.items():
            print(f"Running {model_name} model...")

            try:
                # Create detector
                detector = DeepfakeDetector(
                    model_name=model_name,
                    confidence_threshold=0.5,  # Use default threshold for individual models
                    device=self.device,
                )

                # Set up CSV path for this model
                csv_path = os.path.join(output_folder, f"{model_name}_detections.csv")

                # Run detection
                detections, final_result = detector.detect(
                    media_path=media_path,
                    save_csv=save_csv,
                    csv_path=csv_path,
                    save_annotated=False,  # Don't save annotated media for individual models
                    output_folder=output_folder,
                    num_frames=num_frames,
                )

                # Load the saved CSV into a dataframe
                if save_csv and os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    df["model_name"] = model_name
                    df["weight"] = weight
                    detection_dataframes.append(df)
                    print(f"{model_name} completed. Result: {final_result}")

            except Exception as e:
                print(f"Error running {model_name}: {e}")
                continue

        return detection_dataframes, len(detection_dataframes) > 0

    def _perform_weighted_averaging(
        self, detection_dataframes: List[pd.DataFrame], output_folder: str
    ) -> bool:
        """Perform weighted averaging of detection results.

        Args:
            detection_dataframes: List of dataframes containing detection results
            output_folder: Folder path to save ensemble results

        Returns:
            Final ensemble prediction (True for deepfake, False for real)
        """
        if not detection_dataframes:
            raise ValueError("No detection results to average")

        # Combine all dataframes
        combined_df = pd.concat(detection_dataframes, ignore_index=True)

        # Get unique frame numbers
        frame_numbers = sorted(combined_df["frame_number"].unique())

        ensemble_results = []

        # Process each frame
        for frame_num in frame_numbers:
            frame_data = combined_df[combined_df["frame_number"] == frame_num]

            # Calculate weighted average confidence
            weighted_confidence = 0.0
            total_weight = 0.0

            for _, row in frame_data.iterrows():
                # Convert is_deepfake to probability (1.0 for deepfake, 0.0 for real)
                prob = (
                    row["confidence"]
                    if row["is_deepfake"]
                    else (1.0 - row["confidence"])
                )
                weighted_confidence += prob * row["weight"]
                total_weight += row["weight"]

            # Normalize by total weight
            if total_weight > 0:
                weighted_confidence /= total_weight

            # Determine final prediction
            is_deepfake = weighted_confidence >= self.confidence_threshold
            final_confidence = (
                weighted_confidence if is_deepfake else (1.0 - weighted_confidence)
            )

            ensemble_results.append(
                {
                    "frame_number": frame_num,
                    "is_deepfake": is_deepfake,
                    "confidence": round(final_confidence, 4),
                }
            )

        # Create ensemble results dataframe
        ensemble_df = pd.DataFrame(ensemble_results)

        # Save ensemble results to CSV
        ensemble_csv_path = os.path.join(output_folder, "ensemble_detections.csv")
        ensemble_df.to_csv(ensemble_csv_path, index=False)
        print(f"Ensemble results saved to: {ensemble_csv_path}")

        # Calculate final result (majority vote based on frames)
        deepfake_frames = ensemble_df["is_deepfake"].sum()
        total_frames = len(ensemble_df)
        final_result = deepfake_frames > (total_frames / 2)

        # Save final result to text file
        result_txt_path = os.path.join(output_folder, "pipeline_result.txt")
        with open(result_txt_path, "w") as f:
            f.write(
                f"Final Ensemble Result: {'DEEPFAKE' if final_result else 'REAL'}\n"
            )
            f.write(f"Deepfake frames: {deepfake_frames}/{total_frames}\n")
            f.write(f"Average confidence: {ensemble_df['confidence'].mean():.4f}\n")
            f.write(f"Model configurations: {self.model_configs}\n")

        print(f"Final result saved to: {result_txt_path}")
        print(f"Final Ensemble Result: {'DEEPFAKE' if final_result else 'REAL'}")

        return final_result

    def detect(
        self,
        media_path: str,
        output_folder: str,
        save_csv: bool = True,
        num_frames: int = 11,
    ) -> bool:
        """Run the complete ensemble deepfake detection pipeline.

        Args:
            media_path: Path to the media file (image or video) to analyze
            output_folder: Folder path to save all detection results
            save_csv: Whether to save detection results to CSV files
            num_frames: Number of equally spaced frames for video analysis

        Returns:
            Final ensemble prediction (True for deepfake, False for real)

        Raises:
            FileNotFoundError: If media file doesn't exist
            ValueError: If no detection results are generated
        """
        if not os.path.exists(media_path):
            raise FileNotFoundError(f"Media file not found: {media_path}")

        print("Starting Ensemble Deepfake Detection Pipeline V2...")
        print(f"Model configurations: {self.model_configs}")
        print(f"Media path: {media_path}")
        print(f"Output folder: {output_folder}")
        print(f"Device: {self.device}")

        # Run individual models
        detection_dataframes, success = self._run_individual_models(
            media_path=media_path,
            output_folder=output_folder,
            save_csv=save_csv,
            num_frames=num_frames,
        )

        if success and detection_dataframes:
            # Perform weighted averaging
            final_result = self._perform_weighted_averaging(
                detection_dataframes, output_folder
            )
            print(f"\nEnsemble pipeline completed successfully!")
            return final_result
        else:
            raise ValueError("No detection results were generated.")

    def get_model_info(self) -> Dict:
        """Get information about the ensemble detector.

        Returns:
            Dictionary containing detector information
        """
        return {
            "model_configs": self.model_configs,
            "device": str(self.device),
            "confidence_threshold": self.confidence_threshold,
            "total_models": len(self.model_configs),
        }


# Legacy function for backward compatibility
def run_ensemble_pipeline(
    model_configs: Dict[str, float],
    media_path: str,
    output_folder: str,
    save_csv: bool = True,
    num_frames: int = 11,
) -> bool:
    """Legacy function to run the complete ensemble pipeline.

    Args:
        model_configs: Dictionary mapping model names to their weights
        media_path: Path to the media file (image or video) to analyze
        output_folder: Folder path to save all detection results
        save_csv: Whether to save detection results to CSV files
        num_frames: Number of equally spaced frames for video analysis

    Returns:
        Final ensemble prediction (True for deepfake, False for real)
    """
    detector = PipelineDeepfakeDetection(model_configs)
    return detector.detect(media_path, output_folder, save_csv, num_frames)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Ensemble Deepfake Detection Pipeline V2"
    )
    parser.add_argument(
        "--media_path",
        type=str,
        required=True,
        help="Path to the media file (image or video) to analyze for deepfakes.",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        required=True,
        help="Folder path to save all detection results and ensemble outputs.",
    )
    parser.add_argument(
        "--save_csv",
        action="store_true",
        default=True,
        help="Whether to save detection results to CSV files.",
    )
    parser.add_argument(
        "--num_frames",
        type=int,
        default=11,
        help="Number of equally spaced frames to extract from video for analysis.",
    )

    args = parser.parse_args()

    # Default model configurations with weights
    model_configs = {"resnet_inception": 0.5, "efficientnet": 0.5}

    # Create ensemble detector and run detection
    detector = PipelineDeepfakeDetection(model_configs)
    detector.detect(
        media_path=args.media_path,
        output_folder=args.output_folder,
        save_csv=args.save_csv,
        num_frames=args.num_frames,
    )


if __name__ == "__main__":
    main()
