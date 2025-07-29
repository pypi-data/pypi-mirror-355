"""Parser module."""

import logging
import sys
from pathlib import Path

from fw_gear_form_importer.util import validate_modality

log = logging.getLogger()


def parse_config(context):
    """Parses config.json."""
    file_type = context.get_input("input-file")["object"]["type"]
    file_path = context.get_input("input-file")["location"]["path"]
    tag = context.config.get("tag")
    metadata_location = context.config.get("metadata_location", "")
    # Just not 100% sure if the config will populate this with "None"
    # if it's not provided or not.
    if metadata_location is None:
        metadata_location = ""

    # Get the modality from config, default is empty string (no modality)
    modality = context.config.get("modality", "")
    # Handle special cases for no modality
    if modality in {"None", ""}:
        modality = None

    # Validate modality against Flywheel's valid modalities
    if modality is not None and context.client:
        if not validate_modality(context.client, modality):
            log.error(f"Invalid modality: {modality}")
            sys.exit(1)

    return file_path, file_type, tag, metadata_location, modality


def find_file_type(file_path: Path, type_dict: dict) -> str:
    file_type = None
    name = str(file_path)
    for ft, suffixes in type_dict.items():
        if any([name.endswith(suffix) for suffix in suffixes]):
            file_type = ft
            break
    if file_type is None:
        log.warning("Could not determine file type from suffix.")

    return file_type
