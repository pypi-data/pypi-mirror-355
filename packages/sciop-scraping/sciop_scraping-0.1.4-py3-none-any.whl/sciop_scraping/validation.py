"""
Helper methods for validation that might be used in multiple quests
"""

import hashlib
import re
from pathlib import Path

from tqdm import tqdm

from sciop_scraping.quests.base import ValidationError


def validate_bagit_manifest(path: Path, hash_type: str = "md5") -> list[ValidationError]:
    """
    Given the base directory of a bagit directory that contains `manifest-{hash_type}.txt`
    and `data/` check the files against the manifest,
    returning ValidationErrors for missing or incorrect files.
    """
    errors = []
    manifest_path = path / f"manifest-{hash_type}.txt"

    if not manifest_path.exists():
        errors.append(
            ValidationError(
                type="manifest",
                path=manifest_path,
                msg="No manifest file found at expected location!",
            )
        )
        return errors

    with open(manifest_path) as f:
        manifest = f.read()

    lines = manifest.splitlines()
    # split into (hash, path) pairs
    items = [re.split(r"\s+", line.strip()) for line in lines]

    for item in tqdm(items, desc="Validating files"):
        expected_hash, sub_path = item
        abs_path = path / sub_path
        if not abs_path.exists():
            errors.append(ValidationError(type="missing", path=sub_path, msg="File not found"))
            continue

        with open(abs_path, "rb") as f:
            file_hash = hashlib.file_digest(f, hash_type).hexdigest()

        if file_hash != expected_hash:
            errors.append(ValidationError(type="incorrect", path=sub_path, msg="Hash mismatch"))
    return errors
