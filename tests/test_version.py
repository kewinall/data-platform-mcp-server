import tomllib
from pathlib import Path

from data_platform_mcp import __version__


def test_runtime_version_matches_project_metadata() -> None:
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with project_file.open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]
    assert __version__ == project_version == "0.5.0"
