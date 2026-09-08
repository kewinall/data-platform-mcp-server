from typing import Any

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool = True


class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    columns: list[ColumnInfo] = Field(default_factory=list)


class TableStatistics(BaseModel):
    schema_name: str
    table_name: str
    row_count: int | None = None
    notes: list[str] = Field(default_factory=list)


class TableMetadata(BaseModel):
    source: str
    schema_name: str
    table_name: str
    object_type: str = "TABLE"
    owner: str | None = None
    remarks: str | None = None
    columns: list[ColumnInfo] = Field(default_factory=list)
    projections: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    upstream: str
    downstream: str
    relation: str = "reads_from"


class LineageResult(BaseModel):
    subject: str
    edges: list[LineageEdge] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SqlLineage(BaseModel):
    statement_type: str
    input_tables: list[str] = Field(default_factory=list)
    ctes: list[str] = Field(default_factory=list)


class DagInfo(BaseModel):
    dag_id: str
    state: str
    last_run: str | None = None


class SearchHit(BaseModel):
    source: str
    title: str
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)
