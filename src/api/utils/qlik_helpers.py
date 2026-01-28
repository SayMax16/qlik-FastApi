"""Qlik Sense specific helper functions."""

import re
import random
import string
from typing import Union


def generate_xrfkey() -> str:
    """
    Generate a random X-Qlik-Xrfkey with 16 alphanumeric characters.

    This key is required for Qlik Sense Repository API calls to prevent
    cross-site request forgery (XSRF) attacks.

    Returns:
        str: A 16-character random string of lowercase letters and digits
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))


def validate_app_id(app_id: str) -> bool:
    """
    Validate app ID format (expects GUID-style).

    Args:
        app_id: Application ID to validate

    Returns:
        bool: True if valid GUID format, False otherwise

    Example:
        >>> validate_app_id("5a730580-3c25-4805-a2ef-dd4a71a91cda")
        True
        >>> validate_app_id("invalid-id")
        False
    """
    if not app_id:
        return False
    guid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    return bool(re.match(guid_pattern, app_id))


def escape_qlik_field_name(field_name: str) -> str:
    """
    Escape field name for Qlik expressions when it contains special characters.

    Args:
        field_name: Field name to escape

    Returns:
        str: Escaped field name wrapped in brackets if necessary

    Example:
        >>> escape_qlik_field_name("Sales Amount")
        '[Sales Amount]'
        >>> escape_qlik_field_name("CustomerID")
        'CustomerID'
    """
    if not field_name:
        return ""
    if " " in field_name or any(char in field_name for char in "()[]{}+-*/=<>!@#$%^&"):
        return f"[{field_name}]"
    return field_name


def clean_field_name(field_name: str) -> str:
    """
    Clean field name by removing extra characters and brackets.

    Args:
        field_name: Field name to clean

    Returns:
        str: Cleaned field name without brackets

    Example:
        >>> clean_field_name("[Customer Name]")
        'Customer Name'
    """
    if not field_name:
        return ""

    cleaned = field_name.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]

    return cleaned.strip()


def extract_field_names_from_expression(expression: str) -> list[str]:
    """
    Extract field names from a Qlik expression.

    Args:
        expression: Qlik Sense expression

    Returns:
        list[str]: List of unique field names found in the expression

    Example:
        >>> extract_field_names_from_expression("Sum([Sales Amount]) / Count([Customer ID])")
        ['Sales Amount', 'Customer ID']
    """
    if not expression:
        return []

    # Extract fields in brackets [FieldName]
    bracket_fields = re.findall(r"\[([^\]]+)\]", expression)

    # Extract simple field names from aggregation functions
    simple_fields = re.findall(r"\b\w+\([^()]*\b(\w+)\b[^()]*\)", expression)

    all_fields = bracket_fields + simple_fields
    return list(set(all_fields))


def format_bytes(size_bytes: int) -> str:
    """
    Format byte size to a human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size string (e.g., "1.5 MB", "500 KB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """
    Safe division that handles division by zero returning default value.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if denominator is zero

    Returns:
        float: Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_percentage(part: Union[int, float], total: Union[int, float], decimal_places: int = 1) -> float:
    """
    Calculate percentage with rounding and zero-division handling.

    Args:
        part: Part value
        total: Total value
        decimal_places: Number of decimal places for rounding

    Returns:
        float: Percentage value rounded to specified decimal places
    """
    if total == 0:
        return 0.0
    percentage = (part / total) * 100
    return round(percentage, decimal_places)
