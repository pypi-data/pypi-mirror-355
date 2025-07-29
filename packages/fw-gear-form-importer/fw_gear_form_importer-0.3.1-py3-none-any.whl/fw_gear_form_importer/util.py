"""Util module."""

# <!-- markdown-link-check-disable -->
import logging
import re
import typing as t
from pathlib import Path

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from fw_meta import MetaData

AnyPath = t.Union[str, Path]

log = logging.getLogger(__name__)

# From
# https://gitlab.com/flywheel-io/product/backend/core-api/-/blob/master/core/models/file_types.py
# Since there's no json filetype (falls under "source code"), we must use the source code definition
# but remove all options but json. full source code def: "source code":
# [".c",".py",".cpp",".js",".m",".json",".java",".php",".css",".toml",".yaml",".yml",".sh", ],
FILETYPES = {"source code": [".json"]}
SOURCECODE_TYPES = {"json": [".json"]}
# These values are sanitized by core:
# https://gitlab.com/flywheel-io/product/backend/core-api/-/blob/master/core/mappers/utils.py#L1217
INVALID_STARTING_CHARS = ["_", ".", "$"]


def get_startswith_lstrip_dict(dict_: t.Dict, startswith: str) -> t.Dict:
    """Returns dictionary filtered with keys starting with startswith."""
    res = {}
    for k, v in dict_.items():
        if k.startswith(startswith):
            res[k.split(f"{startswith}.")[1]] = v
    return res


def sanitize_modality(modality: str):
    """Remove invalid characters in modality.

    Args:
        modality (str): Modality string.

    Returns:
        str: Modality with only spaces, alphanumeric and '-'.
    """
    reg = re.compile(r"[^ 0-9a-zA-Z_-]+")
    modality_sanitized = reg.sub("-", modality)
    if modality_sanitized != modality:
        log.info(f"Sanitizing modality {modality} -> {modality_sanitized}")
    return modality_sanitized


def create_metadata(context: GearToolkitContext, fe: t.Dict, meta: MetaData, qc: t.Dict):
    """Populate .metadata.json.

    Args:
        context (GearToolkitContext): The gear context. fe (dict): A dictionary containing the file
        attributes to update. meta (MetaData): A MetaData containing the file "metadata" (parents
        container info) qc (dict): QC information
    """
    file_input = context.get_input("input-file")

    # Add qc information
    context.metadata.add_qc_result(
        file_input,
        "metadata-extraction",
        # TODO: Add FAIL?
        state="PASS",
        data=qc,
    )
    context.metadata.update_file(file_input, info=fe.get("info", {}))
    if fe.get("modality"):
        modality = sanitize_modality(fe.get("modality"))
        context.metadata.update_file(file_input, modality=modality)

    # parent containers update TODO revisit that age cannot be passed
    if "session.age" in meta:
        _ = meta.pop("session.age")
    context.metadata.update_container("session", **get_startswith_lstrip_dict(meta, "session"))
    context.metadata.update_container("subject", **get_startswith_lstrip_dict(meta, "subject"))
    context.metadata.update_container(
        "acquisition", **get_startswith_lstrip_dict(meta, "acquisition")
    )

    # https://flywheelio.atlassian.net/browse/GEAR-868 Subject needs to be updated on session in
    # old-core These two lines make this gear compatible with 15.x.x and 14.x.x
    sub = context.metadata._metadata.pop("subject")
    context.metadata._metadata.get("session").update({"subject": sub})


def validate_metadata_location(metadata_location: str) -> bool:
    """Validate metadata_location string.

    Args:
        metadata_location (str): The location in the file's metadata to save the form contents.

    Returns:
        bool: True if valid, False otherwise.
    """

    if metadata_location is None:
        log.error("metadata_location is blank.")
        return False
    # The metadata location must start with "info" because otherwise there's no way to allow the
    # metadata location config option to be blank, AND specify a default location
    if not metadata_location.startswith("info.") and metadata_location != "info":
        log.error("metadata keys must start with 'info.' or be just 'info'")
        return False
    if any(
        meta_key.startswith(isc)
        for meta_key in metadata_location.split(".")
        for isc in INVALID_STARTING_CHARS
    ):
        log.error("metadata keys cannot start with " + str(INVALID_STARTING_CHARS))
        return False
    return True


def validate_modality(client: flywheel.Client, modality: t.Optional[str]) -> bool:
    """Validate modality against Flywheel's valid modalities.

    Args:
        client (flywheel.Client): The Flywheel client. modality (str, optional): The modality to
        validate.

    Returns:
        bool: True if valid or None, False otherwise.
    """
    # If modality is None, it's valid (no modality will be set)
    if modality is None:
        return True

    try:
        # Get all valid modalities from Flywheel
        valid_modalities = client.get_all_modalities()
        valid_modality_ids = [m.id for m in valid_modalities]

        # Check if the provided modality is in the list of valid modalities
        if modality not in valid_modality_ids:
            log.error(
                f"Invalid modality '{modality}'. Valid modalities are: {', '.join(valid_modality_ids)}"
            )
            return False
        return True
    except Exception as e:
        log.error(f"Error validating modality: {e}")
        return False
