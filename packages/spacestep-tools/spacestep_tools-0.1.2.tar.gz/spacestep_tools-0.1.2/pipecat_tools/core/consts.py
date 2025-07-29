"""Utility helpers for registering and retrieving per‑function constants.

This module acts as a tiny in‑memory registry that lets other parts of the
codebase declare constants required by tool functions (e.g. web‑hook URLs)
and then populate them from JSON files at runtime.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Iterable, List

#: Registry of constants keyed by function name → constant name → value.
_FUNCTION_CONSTANTS = {
    "get_available_time_slots": {
        "webhook_url": None
    },
    "book_appointment": {
        "webhook_url": None
    }
}

def get_required_constants(function_names: Iterable[str]):
    """Return unresolved constants for the supplied functions.

    Args:
        function_names: Iterable of function names to inspect.

    Returns:
        Dict[str, List[str]]: A mapping where each key is a function name
        and the value is a sorted list of constant names that are still
        unset (``None``).
    """
    result: Dict[str, List[str]] = {}
    for fn in function_names:
        consts = _FUNCTION_CONSTANTS.get(fn)
        if consts is None:
            logging.warning("Unknown function name %s", fn)
            continue
        missing = [name for name, value in consts.items() if value is None]
        if missing:
            result[fn] = sorted(missing)
    return result

def get_all_set_constants():
    """Return every constant that already has a value.

    Returns:
        Dict[str, Dict[str, object]]: Mapping of function names to a
        sub‑mapping of constant names and their current values.
    """
    result: Dict[str, Dict[str, object]] = {}
    for fn, consts in _FUNCTION_CONSTANTS.items():
        set_consts = {k: v for k, v in consts.items() if v is not None}
        if set_consts:
            result[fn] = set_consts
    return result


def get_constant(function_name: str, constant_name: str):
    """Fetch a single constant.

    Args:
        function_name: Name of the function whose constant is requested.
        constant_name: The specific constant name to retrieve.

    Returns:
        object: The constant's value.

    Raises:
        KeyError: If the function or constant is not registered.
    """
    try:
        return _FUNCTION_CONSTANTS[function_name][constant_name]
    except KeyError as exc:
        raise KeyError(
            f"Constant '{constant_name}' for function '{function_name}' is not registered."
        ) from exc

def set_constants(path_to_configs: str) -> None:
    """Load constants from JSON files located in a directory.

    Each ``*.json`` file should be named after a function (e.g.
    ``book_appointment.json``) and contain a flat JSON object whose keys
    are constant names.

    Args:
        path_to_configs: Path to the directory containing the JSON files.

    Raises:
        ValueError: If the provided path is not a directory.
    """
    if not os.path.isdir(path_to_configs):
        raise ValueError(f"Path '{path_to_configs}' is not a directory.")

    for entry in os.listdir(path_to_configs):
        if not entry.lower().endswith(".json"):
            continue  # skip non‑JSON files

        function_name = os.path.splitext(entry)[0]
        file_path = os.path.join(path_to_configs, entry)

        try:
            with open(file_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as exc:
            logging.error("Failed to load constants from %s: %s", file_path, exc)
            continue

        if not isinstance(data, dict):
            logging.warning(
                "Constants file %s does not contain a JSON object at the "
                "top level; skipping.",
                file_path,
            )
            continue

        current = _FUNCTION_CONSTANTS.setdefault(function_name, {})
        for const_name, value in data.items():
            if const_name in current and current[const_name] is not None:
                logging.warning(
                    "Overwriting constant '%s' for function '%s' from %s",
                    const_name,
                    function_name,
                    file_path,
                )
            current[const_name] = value