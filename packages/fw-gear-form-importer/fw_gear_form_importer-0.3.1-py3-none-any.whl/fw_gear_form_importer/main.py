import logging
import sys
import typing as t
from pathlib import Path

import flywheel
from fw_meta import MetaData

from .files import json_file
from .parser import find_file_type
from .util import SOURCECODE_TYPES, validate_metadata_location

AnyPath = t.Union[str, Path]

log = logging.getLogger(__name__)


def project_tag_update(project: flywheel.Project = None) -> None:
    """Helper function to update dicom allow/deny tag list."""
    if project:
        log.info("Updating allow/deny tag list from project.info.context.forms.json.")
        # Updating allow/deny tag list from project.info.context.header.dicom
        json_file.update_array_keys(
            project.info.get("context", {}).get("forms", {}).get("json", {})
        )


def run(
    file_type: t.Union[str, None],
    file_path: AnyPath,
    project: flywheel.Project = None,
    metadata_location: str = None,
    modality: t.Optional[str] = None,
) -> t.Tuple[t.Dict, MetaData, t.Dict]:
    """Processes file at file_path.

    Args:
        file_type (str): String defining file type.
        file_path (AnyPath): A Path-like to file input.
        project (flywheel.Project): The flywheel project the file is originating
            (Default: None).
        metadata_location (str): The location in the file's metadata to save the
            form contents (default: None).
        modality (str, optional): The modality to set on the file (default: None).

    Returns:
        dict: Dictionary of file attributes to update.
        dict: Dictionary containing the file meta.
        dict: Dictionary containing the qc metrics.

    """
    if not validate_metadata_location(metadata_location):
        sys.exit(1)

    project_tag_update(project)
    log.info("Processing %s...", file_path)

    # Flywheel classifies json files as "source code" by default.  These checks cover the two
    # most likely scenarios, default classification and unclassified:
    if file_type is None or file_type == "source code":
        code_type = find_file_type(file_path, SOURCECODE_TYPES)
        if code_type is None:
            sys.exit(1)

        fe, meta, qc = json_file.process(
            file_path, metadata_location, remove_blanks=True, modality=modality
        )
        return fe, meta, qc

    else:
        log.error(f"File type {file_type} is not supported currently.")
        sys.exit(1)
