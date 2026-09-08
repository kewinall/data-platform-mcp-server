import hashlib
import re

from sqlglot import exp, parse
from sqlglot.errors import ParseError

_FORBIDDEN_NODE_NAMES = {
    "Alter",
    "Analyze",
    "Command",
    "Commit",
    "Copy",
    "Create",
    "Delete",
    "Drop",
    "Execute",
    "Grant",
    "Insert",
    "Into",
    "Merge",
    "Revoke",
    "Rollback",
    "Set",
    "Transaction",
    "Truncate",
    "Update",
    "Use",
    "Vacuum",
}
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|merge|drop|alter|truncate|create|grant|revoke|copy|call|do|"
    r"vacuum|analyze|refresh|execute|commit|rollback)\b",
    re.IGNORECASE,
)


def normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split())


def _parse_single_query(sql: str) -> exp.Expression:
    try:
        statements = [statement for statement in parse(sql) if statement is not None]
    except ParseError as exc:
        raise ValueError("SQL could not be parsed safely") from exc

    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is allowed")

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        raise ValueError("Only query expressions are allowed")

    for node in statement.walk():
        if type(node).__name__ in _FORBIDDEN_NODE_NAMES:
            raise ValueError(f"SQL contains forbidden expression: {type(node).__name__}")
    return statement


def ensure_read_only_sql(sql: str) -> str:
    normalized = normalize_sql(sql)
    if not normalized:
        raise ValueError("SQL must not be empty")

    if ";" in normalized.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed")
    normalized = normalized.rstrip(";")

    lowered = normalized.lower()
    if lowered.startswith("explain "):
        inner = normalized.split(None, 1)[1]
        return "EXPLAIN " + ensure_read_only_sql(inner)

    if lowered.startswith("show "):
        if _FORBIDDEN_KEYWORDS.search(normalized):
            raise ValueError("SHOW statement contains a forbidden keyword")
        try:
            statements = [statement for statement in parse(normalized) if statement is not None]
        except ParseError as exc:
            raise ValueError("SHOW statement could not be parsed safely") from exc
        if len(statements) != 1:
            raise ValueError("Exactly one SQL statement is allowed")
        return normalized

    _parse_single_query(normalized)
    return normalized


def sql_fingerprint(sql: str) -> str:
    normalized = normalize_sql(sql)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
