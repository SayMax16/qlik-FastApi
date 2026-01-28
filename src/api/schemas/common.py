"""Common Pydantic schemas used across the API."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    qlik_connected: bool | None = Field(None, description="Qlik Sense connection status")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: str | None = Field(None, description="Field name if error is field-specific")
    message: str = Field(..., description="Error message")
    type: str | None = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type or category")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    details: dict[str, Any] | list[ErrorDetail] | None = Field(
        None, description="Additional error details"
    )
    request_id: str | None = Field(None, description="Request ID for tracking")


class PaginationParams(BaseModel):
    """Pagination parameters schema."""

    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of items to return")


class SortParams(BaseModel):
    """Sort parameters schema."""

    sort_by: str = Field(default="name", description="Field to sort by")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class PaginationMeta(BaseModel):
    """Pagination metadata schema."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_records: int = Field(..., description="Total number of records")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    has_more: bool = Field(..., description="Whether there are more items available")


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Whether operation was successful")
    data: dict[str, Any] | None = Field(None, description="Additional response data")
