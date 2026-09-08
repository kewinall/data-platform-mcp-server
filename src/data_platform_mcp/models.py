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


class DagInfo(BaseModel):
    dag_id: str
    state: str
    last_run: str | None = None


class SearchHit(BaseModel):
    source: str
    title: str
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)
