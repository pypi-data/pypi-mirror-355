import doctest
from pathlib import Path

import pytest

import when_exactly as we

FILES = [f for f in Path("./docs/").rglob("*.md")]


@pytest.mark.parametrize(
    "file",
    FILES,
    ids=[f.name for f in FILES],
)  # type: ignore
def test_docs(file: Path) -> None:
    file_str = str(file)
    test_results = doctest.testfile(
        filename=file_str,
        module_relative=False,
        globs={"we": we},
    )

    assert test_results.failed == 0
