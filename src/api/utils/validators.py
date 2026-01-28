"""Validation utility functions."""

import re
from typing import Any


def validate_app_id(app_id: str) -> bool:
    """
    Validate Qlik Sense application ID format.

    Args:
        app_id: Application ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Qlik app IDs are typically GUIDs
    guid_pattern = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    return bool(guid_pattern.match(app_id))


def validate_object_id(object_id: str) -> bool:
    """
    Validate Qlik Sense object ID format.

    Args:
        object_id: Object ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Object IDs can be various formats (GUID or custom)
    if not object_id or len(object_id) > 255:
        return False
    return True


def validate_field_name(field_name: str) -> bool:
    """
    Validate Qlik Sense field name.

    Args:
        field_name: Field name to validate

    Returns:
        True if valid, False otherwise
    """
    if not field_name or len(field_name) > 255:
        return False
    # Field names should not contain certain special characters
    invalid_chars = ["\n", "\r", "\t"]
    return not any(char in field_name for char in invalid_chars)
