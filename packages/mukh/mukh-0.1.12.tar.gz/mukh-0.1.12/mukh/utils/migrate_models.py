"""
Compact model migration script for Hugging Face Hub.

Usage:
    python mukh/utils/migrate_models.py --upload SOURCE TARGET REPO
    python mukh/utils/migrate_models.py --scan DIR
    python mukh/utils/migrate_models.py --clean DIR
    python mukh/utils/migrate_models.py --patterns PATTERN1 PATTERN2

Example:
    python mukh/utils/migrate_models.py --upload mukh/face_detection/models/blazeface face_detection/blazeface ishandutta/mukh-models
    python mukh/utils/migrate_models.py --patterns "*.pth" "*.bin" "*.safetensors" "*.onnx" "*.npy" "*.txt" "*.tar" "*.pt"
"""

import argparse
import os
from pathlib import Path

from huggingface_hub import HfApi, login, whoami

default_patterns = [
    "*.pth",
    "*.bin",
    "*.safetensors",
    "*.onnx",
    "*.npy",
    "*.txt",
    "*.tar",
    "*.pt",
]


def authenticate():
    """Authenticate with HF Hub."""
    try:
        whoami()
        return HfApi()
    except:
        import getpass

        token = getpass.getpass("HF Token: ")
        login(token)
        return HfApi()


def upload_files(source_dir, target_dir, repo_id, patterns=None):
    """Upload files matching patterns to HF repo."""
    api = authenticate()
    source_path = Path(source_dir)
    patterns = patterns or default_patterns

    uploaded = 0
    for pattern in patterns:
        for file_path in source_path.rglob(pattern):
            # Calculate relative path for repo
            rel_path = file_path.relative_to(source_path)
            repo_path = f"{target_dir}/{rel_path}" if target_dir else str(rel_path)

            try:
                api.upload_file(
                    path_or_fileobj=str(file_path),
                    path_in_repo=repo_path,
                    repo_id=repo_id,
                    repo_type="model",
                )
                print(f"✓ {file_path.name} -> {repo_path}")
                uploaded += 1
            except Exception as e:
                print(f"✗ {file_path.name}: {e}")

    print(f"\n{uploaded} files uploaded to {repo_id}")
    return uploaded > 0


def scan_directory(directory, patterns=None):
    """Show files that would be uploaded."""
    patterns = patterns or default_patterns
    path = Path(directory)

    print(f"\nScanning {directory}:")
    total_size = 0
    for pattern in patterns:
        files = list(path.rglob(pattern))
        if files:
            print(f"\n{pattern}:")
            for f in files:
                size_mb = f.stat().st_size / (1024**2)
                total_size += size_mb
                print(f"  {f.name} ({size_mb:.1f}MB)")

    print(f"\nTotal: {total_size:.1f}MB")


def clean_files(directory, patterns=None):
    """Remove model files from directory."""
    patterns = patterns or default_patterns
    path = Path(directory)

    removed = 0
    for pattern in patterns:
        for file_path in path.rglob(pattern):
            file_path.unlink()
            print(f"✓ Removed {file_path.name}")
            removed += 1

    print(f"\n{removed} files removed")


def main():
    parser = argparse.ArgumentParser(description="Upload models to Hugging Face")
    parser.add_argument(
        "--upload",
        nargs=3,
        metavar=("SOURCE", "TARGET", "REPO"),
        help="Upload: source_dir target_dir repo_id",
    )
    parser.add_argument("--scan", help="Scan directory for models")
    parser.add_argument("--clean", help="Remove model files from directory")
    parser.add_argument("--patterns", nargs="+", help="File patterns to match")

    args = parser.parse_args()

    if args.upload:
        source, target, repo = args.upload
        upload_files(source, target, repo, args.patterns)

    elif args.scan:
        scan_directory(args.scan, args.patterns)

    elif args.clean:
        clean_files(args.clean, args.patterns)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
