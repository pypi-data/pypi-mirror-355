"""JSON parsing class."""

import logging
import sys
import typing as t

from fw_meta import MetaData
from fw_utils import AnyPath

from .fw_file_json import JSON

log = logging.getLogger(__name__)

DENY_KEYS = set()
ALLOW_KEYS = set()
METADATA_PREFIX = "info"


def update_array_keys(custom_tags: t.Dict[str, bool]) -> None:
    """Update DENY_KEYS and ALLOW_KEYS list.

    Args:
        custom_tags (dict): Dictionary of type with key/value of type key: bool.
            If bool=True, key is added to ALLOW_KEYS. If bool=False, tag is removed
            from ALLOW_KEYS.
    """
    if custom_tags:
        # validate key/value
        for k, v in custom_tags.items():
            if isinstance(v, str):
                if v.strip().lower() == "false":
                    custom_tags[k] = False
                elif v.strip().lower() == "true":
                    custom_tags[k] = True
                else:
                    log.error(
                        "Invalid value defined in project.info.forms.json "
                        "for key %s. Valid value is boolean, 'True' or 'False'",
                        k,
                    )
                    sys.exit(1)

        for k, bool_val in custom_tags.items():
            if bool_val:
                if k not in ALLOW_KEYS:
                    ALLOW_KEYS.add(k)
            else:
                if k in ALLOW_KEYS:
                    ALLOW_KEYS.remove(k)
                if k not in DENY_KEYS:
                    DENY_KEYS.add(k)


def get_fw_filtered_fields(json_file: JSON) -> None:
    """filters json fields based on flywheel ALLOW and DENY lists

    if ALLOW_KEYS has values, only those values are returned.
    if DENY_KEYS has values, those values are removed and the rest are returned.

    ALLOW_KEYS has precedent over DENY_KEYS, if ALLOW_KEYS and DENY_KEYS both have values,
    DENY_KEYS will be ignored.
    Args:
        json_file: the fw-file json representation

    """

    log.debug(f"ALLOW_KEYS: {ALLOW_KEYS}")
    if ALLOW_KEYS:
        current_keys = json_file.get_all_keys()
        for key in current_keys:
            # using startswith captures nested keys.
            if (
                not any([allow_tag.startswith(key) for allow_tag in ALLOW_KEYS])
                and key in json_file.keys()
            ):
                del json_file[key]
        return

    else:
        log.debug(f"DENY_KEYS: {DENY_KEYS}")
        for dt in DENY_KEYS:
            del json_file[dt]
        return


def process(
    file_path: AnyPath,
    metadata_location: str,
    remove_blanks: bool = True,
    modality: t.Optional[str] = None,
) -> t.Tuple[t.Dict, MetaData, t.Dict]:
    """Process `file_path` and returns a `flywheel.FileEntry` and its corresponding meta.

    Args:
        file_path (Path-like): Path to input-file.
        metadata_location: str: The location in the file's metadata to save the json contents to
        remove_blanks (bool): If true, exclude all keys with blank or empty string values
        modality (str, optional): The modality to set on the file (default: None).

    Returns:
        fe (dict): Dictionary of file attributes to update.
        file_meta (dict): Dictionary containing the file meta.
        qc (dict): Dictionary containing the qc metrics.
    """

    json_file = JSON(file_path)
    if remove_blanks:
        json_file.remove_blanks()

    file_meta = json_file.get_meta()
    get_fw_filtered_fields(json_file)

    fe = generate_file_entry(json_file.to_dict(), metadata_location, modality)
    qc = {}
    return fe, file_meta, qc


def generate_file_entry(
    file_dict: dict, metadata_location: str, modality: t.Optional[str] = None
) -> dict:
    """Generate metadata dictionary.

    The metadata_location must start with METADATA_PREFIX, in this case "info".
    If the location is JUST "info", everything will populate at the top level.
    If the location is info.something, it will populate under "something" as
    a metadata object.

    Args:
        file_meta (dict): Dictionary containing the file meta.
        metadata_location (str): The location to place the metadata in the file.
        modality (str, optional): The modality to set on the file (default: None).

    Returns:
        dict: Metadata dictionary.
    """

    if metadata_location == METADATA_PREFIX or metadata_location is None:
        metadata_location = ""
    elif metadata_location.startswith(f"{METADATA_PREFIX}."):
        metadata_location = metadata_location[len(METADATA_PREFIX) + 1 :]

    metadata = {METADATA_PREFIX: {}}
    inner_metadata = metadata[METADATA_PREFIX]

    if metadata_location:
        keys = metadata_location.split(".")
        for key in keys:
            inner_metadata = inner_metadata.setdefault(key, {})

    inner_metadata.update(file_dict)

    file_entry = {METADATA_PREFIX: metadata[METADATA_PREFIX]}
    # Only add modality if it's not None
    if modality is not None:
        file_entry["modality"] = modality
    return file_entry
