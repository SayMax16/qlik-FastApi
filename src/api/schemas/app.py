"""Pydantic schemas for Qlik Sense application models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AppBase(BaseModel):
    """Base schema for Qlik Sense application."""

    name: str = Field(..., description="Application name")
    description: str | None = Field(None, description="Application description")


class AppMetadata(BaseModel):
    """Application metadata schema."""

    app_id: str = Field(..., alias="qDocId", description="Application ID")
    name: str = Field(..., alias="qDocName", description="Application name")
    title: str = Field(..., alias="qTitle", description="Application title")
    thumbnail: str | None = Field(None, alias="qThumbnail", description="Application thumbnail")
    last_reload_time: str | None = Field(
        None, alias="qLastReloadTime", description="Last reload time"
    )
    modified_date: str | None = Field(None, alias="qModifiedDate", description="Last modified date")
    file_size: int | None = Field(None, alias="qFileSize", description="File size in bytes")
    published: bool = Field(False, description="Whether app is published")
    stream_name: str | None = Field(None, description="Stream name if published")


class AppInfo(BaseModel):
    """Detailed application information schema."""

    app_id: str = Field(..., description="Application ID")
    name: str = Field(..., description="Application name")
    description: str | None = Field(None, description="Application description")
    published: bool = Field(..., description="Whether app is published")
    stream: str | None = Field(None, description="Stream name if published")
    owner: str | None = Field(None, description="App owner")
    last_reload_time: datetime | None = Field(None, description="Last reload time")
    file_size: int | None = Field(None, description="File size in bytes")
    thumbnail: str | None = Field(None, description="Thumbnail URL")


class AppListResponse(BaseModel):
    """Response schema for list of applications."""

    apps: list[AppMetadata] = Field(..., description="List of applications")
    total: int = Field(..., description="Total number of applications")


class AppObjectMeta(BaseModel):
    """Schema for application object metadata."""

    object_id: str = Field(..., alias="qInfo.qId", description="Object ID")
    object_type: str = Field(..., alias="qInfo.qType", description="Object type")
    title: str | None = Field(None, description="Object title")
    description: str | None = Field(None, description="Object description")
    published: bool = Field(False, description="Whether object is published")
    approved: bool = Field(False, description="Whether object is approved")


class AppObjectsResponse(BaseModel):
    """Response schema for list of application objects."""

    app_id: str = Field(..., description="Application ID")
    objects: list[dict[str, Any]] = Field(..., description="List of objects")
    total: int = Field(..., description="Total number of objects")


class AppSelectionState(BaseModel):
    """Schema for application selection state."""

    app_id: str = Field(..., description="Application ID")
    selections: list[dict[str, Any]] = Field(..., description="Current selections")
    locked_fields: list[str] = Field(default_factory=list, description="Locked field names")


class TableInfo(BaseModel):
    """Schema for table information."""

    table_name: str = Field(..., description="Table name")
    field_count: int = Field(..., description="Number of fields in table")
    estimated_rows: int | None = Field(None, description="Estimated number of rows")


class TableListResponse(BaseModel):
    """Response for list of tables."""

    app_name: str = Field(..., description="Application name")
    tables: list[TableInfo] = Field(..., description="List of tables")


class AppScriptResponse(BaseModel):
    """Response schema for app script."""

    app_id: str = Field(..., description="Application ID")
    script: str = Field(..., description="Load script content")
    sections: list[dict[str, str]] | None = Field(None, description="Script sections")


class DimensionDefinition(BaseModel):
    """Schema for dimension definition."""

    field: str = Field(..., description="Field name or expression")
    label: str | None = Field(None, description="Dimension label")


class MeasureDefinition(BaseModel):
    """Schema for measure definition."""

    expression: str = Field(..., description="Measure expression")
    label: str | None = Field(None, description="Measure label")
    number_format: dict[str, Any] | None = Field(None, description="Number format settings")


class ObjectDefinitionResponse(BaseModel):
    """Response schema for object dimensions and measures."""

    object_id: str = Field(..., description="Object ID")
    object_type: str = Field(..., description="Object type (e.g., pivot-table, barchart)")
    app_name: str = Field(..., description="Application name")
    app_id: str = Field(..., description="Application ID")
    dimensions: list[DimensionDefinition] = Field(..., description="List of dimensions")
    measures: list[MeasureDefinition] = Field(..., description="List of measures")
