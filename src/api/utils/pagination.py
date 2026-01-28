"""Pagination utility functions."""

from typing import Any, TypeVar

from src.api.schemas.common import PaginatedResponse

T = TypeVar("T")


def paginate(
    items: list[T],
    total: int,
    skip: int,
    limit: int,
) -> PaginatedResponse[T]:
    """
    Create a paginated response from a list of items.

    Args:
        items: List of items for the current page
        total: Total number of items available
        skip: Number of items skipped
        limit: Maximum number of items per page

    Returns:
        PaginatedResponse with items and pagination metadata
    """
    has_more = (skip + len(items)) < total

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )
