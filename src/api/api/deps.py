"""Common API dependencies."""

from typing import Annotated

from fastapi import Depends, Query

from src.api.schemas.common import PaginationParams, SortParams


async def get_pagination_params(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> PaginationParams:
    """Dependency to extract pagination parameters from query string."""
    return PaginationParams(skip=skip, limit=limit)


async def get_sort_params(
    sort_by: Annotated[str, Query()] = "name",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> SortParams:
    """Dependency to extract sort parameters from query string."""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
SortDep = Annotated[SortParams, Depends(get_sort_params)]
