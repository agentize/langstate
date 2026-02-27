"""JSON diff utilities for the in-memory snapshot repository."""

from __future__ import annotations

import json
from typing import cast, Dict, List, Mapping


def compute_delta(
    old_json: Mapping[str, object], new_json: Mapping[str, object]
) -> Dict[str, object]:
    """Compute a delta between two flat JSON dicts.

    Returns a dict with keys:
        added   — keys present only in *new_json*
        removed — keys present only in *old_json*
        modified — keys whose values differ
    """
    old_keys = set(old_json.keys())
    new_keys = set(new_json.keys())

    added = {k: new_json[k] for k in new_keys - old_keys}
    removed = list(old_keys - new_keys)
    modified = {
        k: new_json[k]
        for k in old_keys & new_keys
        if json.dumps(old_json[k], sort_keys=True, default=str)
        != json.dumps(new_json[k], sort_keys=True, default=str)
    }

    delta: Dict[str, object] = {}
    if added:
        delta["added"] = added
    if removed:
        delta["removed"] = removed
    if modified:
        delta["modified"] = modified
    return delta


def apply_delta(
    base_json: Mapping[str, object], delta: Mapping[str, object]
) -> Dict[str, object]:
    """Apply a delta to a base dict, producing the new dict."""
    result = dict(base_json)

    added = delta.get("added")
    if isinstance(added, dict):
        result.update(cast(Dict[str, object], added))

    removed = delta.get("removed")
    if isinstance(removed, list):
        for key in cast(List[str], removed):
            result.pop(key, None)

    modified = delta.get("modified")
    if isinstance(modified, dict):
        result.update(cast(Dict[str, object], modified))

    return result
