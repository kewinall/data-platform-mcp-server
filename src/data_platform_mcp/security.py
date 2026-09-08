import re

_READ_ONLY_PREFIXES = ("select", "with", "explain", "show")
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|drop|alter|truncate|create|grant|revoke|copy|call|do|"
    r"vacuum|analyze|refresh)\b",
    re.IGNORECASE,
)


def normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split())


def ensure_read_only_sql(sql: str) -> str:
    normalized = normalize_sql(sql)
    if not normalized:
        raise ValueError("SQL must not be empty")

    lowered = normalized.lower()
    if not lowered.startswith(_READ_ONLY_PREFIXES):
        raise ValueError("Only read-only SQL is allowed")
    if _FORBIDDEN.search(normalized):
        raise ValueError("SQL contains a forbidden write or DDL keyword")
    if ";" in normalized.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed")
    return normalized.rstrip(";")
