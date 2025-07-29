"""json file class."""

import json
import logging
import typing as t

from dotty_dict import Dotty, dotty
from fw_file.base import AnyPath, File

log = logging.getLogger("FW-JSON")


class JSON(File):
    """Json file format."""

    def __init__(self, file: AnyPath) -> None:
        """Read and parse a .json file.

        Args:
            file (AnyPath): File to load.
        """

        super().__init__(file)
        object.__setattr__(self, "fields", load_json(self.file))

    def save(self, file: AnyPath = None) -> None:  # type: ignore
        fields_out = self.to_dict()

        with open(file, "w") as outfile:
            json.dump(fields_out, outfile)

    def __getitem__(self, key: str):
        """Get key value by name (or "dotty" name e.g. "key1.key2")"""
        return self.fields[key]

    def __setitem__(self, key: str, value) -> None:
        """Set key value by name (or "dotty" name e.g. "key1.key2") and value."""
        self.fields[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete key value by name (or "dotty" name e.g. "key1.key2") and value."""
        if key in self.fields:
            del self.fields[key]

    def __iter__(self):
        """Return iterator over object fields (top level keys only)."""
        return iter(dict(self.fields))

    def __len__(self) -> int:
        """Return the number of top level keys."""
        return len(self.fields)

    def to_dict(self) -> dict:
        return self.fields.to_dict()

    def remove_blanks(self) -> None:
        """Remove blanks from the fields (recursively)."""

        sorted_keys = self.get_all_keys(sort=True, reverse=True)
        for key in sorted_keys:
            # Keys are guaranteed to exist
            if self.fields[key] in ["", None, {}, [], set()]:
                del self[key]
                log.debug(f"removed empty key {key}")

    @staticmethod
    def _get_all_keys(d: t.Union[Dotty, dict]) -> list:
        """"""
        keys = []
        for k, v in d.items():
            keys += [k]
            if isinstance(v, (Dotty, dict)):
                subkeys = JSON._get_all_keys(v)
                keys += [f"{k}.{sk}" for sk in subkeys]
        return keys

    def get_all_keys(self, sort: bool = True, reverse: bool = True) -> list:
        """Return all keys (even nested) from the object, optionally filtered."""
        keys = self._get_all_keys(self.fields)
        if sort:
            keys = sorted(keys, key=lambda x: x.count("."), reverse=reverse)

        return keys


def load_json(file: AnyPath) -> t.Dict[str, t.Any]:
    """Parse json file."""

    try:
        fields = json.load(file)
    except Exception as e:
        log.error("Error Loading JSON File")
        raise e

    fields = dotty(fields)

    return fields
