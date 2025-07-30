"""Model Hub utility for downloading and caching models from Hugging Face.

This module provides utilities to download model files from Hugging Face Hub
and cache them locally for efficient reuse.

Note: This downloads from a public repository and does not require authentication
for end users.
"""

import os
from pathlib import Path
from typing import Optional

from huggingface_hub import hf_hub_download


def download_model(
    filename: str,
    subfolder: Optional[str] = None,
    repo_id: str = "ishandutta/mukh-models",
    cache_dir: Optional[str] = None,
    force_download: bool = False,
) -> str:
    """Download a model file from Hugging Face Hub.

    This downloads from a public repository and requires no authentication.

    Args:
        filename: Name of the file to download
        subfolder: Optional subfolder within the repository
        repo_id: Hugging Face repository ID for the models
        cache_dir: Optional custom cache directory. If None, uses default HF cache.
        force_download: Whether to force re-download even if cached

    Returns:
        Local path to the downloaded model file

    Raises:
        Exception: If download fails or file not found
    """
    try:
        # Check if file exists in cache first (unless force_download is True)
        if not force_download:
            try:
                # Try to get the file without downloading (will raise if not cached)
                file_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    subfolder=subfolder,
                    cache_dir=cache_dir,
                    local_files_only=True,
                    token=False,
                )
                return file_path
            except Exception:
                # File not in cache, need to download
                print(
                    f"Downloading {filename} from Hugging Face Hub (no authentication required)..."
                )

        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            subfolder=subfolder,
            cache_dir=cache_dir,
            force_download=force_download,
            token=False,  # Explicitly disable token for public downloads
        )

        if not force_download:
            print(f"✅ {filename} downloaded successfully!")

        return file_path
    except Exception as e:
        error_msg = f"Failed to download {filename} from {repo_id}"
        if "401" in str(e) or "authentication" in str(e).lower():
            error_msg += "\n\nThis may indicate the repository is private or requires authentication."
            error_msg += (
                "\nPlease ensure the repository is public for end users to access."
            )
        elif "404" in str(e) or "not found" in str(e).lower():
            error_msg += "\n\nThe model file was not found in the repository."
            error_msg += f"\nPlease check if {filename} exists in {subfolder or 'root'} of {repo_id}"
        else:
            error_msg += f"\nError details: {str(e)}"

        raise Exception(error_msg)


def download_blazeface_models() -> tuple[str, str]:
    """Download BlazeFace model files.

    Downloads from public repository without requiring authentication.

    Returns:
        Tuple of (weights_path, anchors_path)

    Raises:
        Exception: If download fails
    """
    try:
        weights_path = download_model(
            "blazeface.pth", subfolder="face_detection/blazeface"
        )
        anchors_path = download_model(
            "anchors.npy", subfolder="face_detection/blazeface"
        )
        return weights_path, anchors_path
    except Exception as e:
        raise Exception(f"Failed to download BlazeFace models: {str(e)}")


def download_ultralight_model(model_variant: str = "RFB-320") -> tuple[str, str]:
    """Download UltraLight model files.

    Downloads from public repository without requiring authentication.

    Args:
        model_variant: Model variant to download ("RFB-320", "RFB-640", "slim-320", "slim-640")

    Returns:
        Tuple of (weights_path, labels_path)

    Raises:
        Exception: If download fails
    """
    try:
        weights_filename = f"version-{model_variant}.pth"
        weights_path = download_model(
            weights_filename, subfolder="face_detection/ultralight"
        )
        labels_path = download_model(
            "voc-model-labels.txt", subfolder="face_detection/ultralight"
        )
        return weights_path, labels_path
    except Exception as e:
        raise Exception(
            f"Failed to download UltraLight models for variant {model_variant}: {str(e)}"
        )


def download_reenactment_model(model_name: str = "vox") -> str:
    """Download reenactment model checkpoint.

    Downloads only the model checkpoint from public repository without requiring authentication.
    Config files are downloaded separately using download_reenactment_config().

    Args:
        model_name: Model name to download ("vox", "ted", "taichi")

    Returns:
        Local path to the downloaded model checkpoint

    Raises:
        Exception: If download fails
    """
    try:
        model_filename = f"{model_name}.pth.tar"
        model_path = download_model(
            model_filename, subfolder="face_reenactment/thin_plate_spline"
        )
        return model_path
    except Exception as e:
        raise Exception(
            f"Failed to download reenactment model for {model_name}: {str(e)}"
        )


def download_reenactment_config(model_name: str = "vox") -> str:
    """Download reenactment model config file.

    Downloads the configuration file for the specified reenactment model from
    public repository without requiring authentication.

    Args:
        model_name: Model name to download config for ("vox", "ted", "taichi", "mgif")

    Returns:
        Local path to the downloaded config file

    Raises:
        Exception: If download fails
    """
    try:
        # Map model names to their corresponding config files
        config_mapping = {
            "vox": "vox-256.yaml",
            "ted": "ted-384.yaml",
            "taichi": "taichi-256.yaml",
            "mgif": "mgif-256.yaml",
        }

        if model_name not in config_mapping:
            raise ValueError(
                f"Unknown model name: {model_name}. "
                f"Available models: {list(config_mapping.keys())}"
            )

        config_filename = config_mapping[model_name]
        config_path = download_model(
            config_filename, subfolder="face_reenactment/thin_plate_spline/config"
        )
        return config_path
    except Exception as e:
        raise Exception(
            f"Failed to download reenactment config for {model_name}: {str(e)}"
        )


def download_resnet_inception_model(
    model_path: str = "resnetinceptionv1_epoch_32.pth",
) -> str:
    """Download ResNet Inception model checkpoint.

    Downloads only the model checkpoint from public repository without requiring authentication.
    Config files remain bundled with the package.
    """
    try:
        model_path = download_model(
            model_path, subfolder="deepfake_detection/resnet_inception"
        )
        return model_path
    except Exception as e:
        raise Exception(f"Failed to download ResNet Inception model: {str(e)}")


def download_efficientnet_model(model_key: str) -> str:
    """Download EfficientNet model checkpoint from Hugging Face Hub.

    Downloads EfficientNet deepfake detection model weights from public repository
    without requiring authentication.

    Args:
        model_key: Model key in format "ModelName_Dataset" (e.g., "EfficientNetB4_DFDC")

    Returns:
        Local path to the downloaded model file

    Raises:
        Exception: If download fails or model not found
    """
    try:
        # Map model keys to their filenames
        filename_mapping = {
            "EfficientNetAutoAttB4_DFDC": "EfficientNetAutoAttB4_DFDC_bestval-72ed969b2a395fffe11a0d5bf0a635e7260ba2588c28683630d97ff7153389fc.pth",
            "EfficientNetB4_DFDC": "EfficientNetB4_DFDC_bestval-c9f3663e2116d3356d056a0ce6453e0fc412a8df68ebd0902f07104d9129a09a.pth",
            "efficientnet-b4": "efficientnet-b4-6ed6700e.pth",
        }

        if model_key not in filename_mapping:
            available_keys = list(filename_mapping.keys())
            raise ValueError(
                f"Unknown model key: {model_key}. "
                f"Available models: {available_keys}\n"
                f"Note: Only DFDC variants are available as fallback. "
                f"Other variants (FFPP, ST) are not uploaded to Hugging Face Hub."
            )

        filename = filename_mapping[model_key]
        model_path = download_model(
            filename, subfolder="deepfake_detection/efficientnet"
        )
        return model_path
    except Exception as e:
        raise Exception(
            f"Failed to download EfficientNet model for {model_key}: {str(e)}"
        )
