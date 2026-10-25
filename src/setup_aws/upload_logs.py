"""Extract the flaws.cloud CloudTrail archive and upload the log files to S3.

Run once from the project root:
    python src/setup_aws/upload_logs.py
"""
import sys
import tarfile
from pathlib import Path

import boto3

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def extract_archive(archive: Path, target_dir: Path) -> None:
    """Extract the tar archive once; skip if already extracted."""
    if target_dir.exists() and any(target_dir.rglob("*.json.gz")):
        print(f"Already extracted: {target_dir}")
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        # The 'data' filter blocks unsafe paths inside an untrusted archive
        tar.extractall(target_dir, filter="data")
    print(f"Extracted to {target_dir}")


def find_log_files(folder: Path) -> list[Path]:
    """Return all gzipped CloudTrail JSON files, sorted by name."""
    return sorted(folder.rglob("*.json.gz"))


def existing_keys(s3, bucket: str, prefix: str) -> set[str]:
    """Return the object keys already in the bucket under the prefix."""
    keys = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        keys.update(obj["Key"] for obj in page.get("Contents", []))
    return keys


def upload_files(files: list[Path], bucket: str, prefix: str) -> None:
    """Upload each file to s3://bucket/prefix, skipping files already there."""
    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    s3 = session.client("s3")
    already = existing_keys(s3, bucket, prefix)
    for i, path in enumerate(files, start=1):
        key = prefix + path.name
        if key in already:
            print(f"[{i}/{len(files)}] skip {path.name} (already uploaded)")
            continue
        s3.upload_file(str(path), bucket, key)
        print(f"[{i}/{len(files)}] uploaded {path.name}")


def main() -> None:
    """Extract the archive and upload all log files."""
    if not config.S3_BUCKET:
        sys.exit("S3_BUCKET is empty. Copy .env.example to .env and set it.")
    if not config.LOGS_ARCHIVE.exists():
        sys.exit(f"Archive not found: {config.LOGS_ARCHIVE}")
    extract_archive(config.LOGS_ARCHIVE, config.LOGS_EXTRACTED_DIR)
    files = find_log_files(config.LOGS_EXTRACTED_DIR)
    print(f"Found {len(files)} log files")
    upload_files(files, config.S3_BUCKET, config.S3_LOGS_PREFIX)
    print(f"Done: s3://{config.S3_BUCKET}/{config.S3_LOGS_PREFIX}")


if __name__ == "__main__":
    main()
