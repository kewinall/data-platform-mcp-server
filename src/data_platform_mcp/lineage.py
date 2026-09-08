from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from data_platform_mcp.models import SqlLineage
from data_platform_mcp.security import ensure_read_only_sql


def analyze_sql_lineage(sql: str) -> SqlLineage:
    safe_sql = ensure_read_only_sql(sql)
    if safe_sql.lower().startswith("show "):
        return SqlLineage(statement_type="SHOW")
    if safe_sql.lower().startswith("explain "):
        safe_sql = safe_sql.split(None, 1)[1]

    try:
        statement = parse_one(safe_sql)
    except ParseError as exc:
        raise ValueError("SQL lineage could not be parsed") from exc

    ctes = sorted(
        {
            cte.alias_or_name
            for cte in statement.find_all(exp.CTE)
            if cte.alias_or_name
        }
    )
    cte_names = {name.lower() for name in ctes}

    inputs: set[str] = set()
    for table in statement.find_all(exp.Table):
        name = table.name
        if not name:
            continue
        if not table.db and name.lower() in cte_names:
            continue

        parts = [part for part in (table.catalog, table.db, name) if part]
        inputs.add(".".join(parts))

    return SqlLineage(
        statement_type=type(statement).__name__.upper(),
        input_tables=sorted(inputs),
        ctes=ctes,
    )
