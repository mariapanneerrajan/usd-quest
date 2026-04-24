"""Golden-solution and bad-mutation tests for every shipped mission.

Every mission must (a) pass when given a known-good authored stage and
(b) reject a set of known-bad mutations with the expected objective failing.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Bootstrap before importing pxr.
from usdquest.packaging.usd_bootstrap import bootstrap

bootstrap()

from usdquest.lessons.grader import grade  # noqa: E402
from usdquest.lessons.mission import load_mission  # noqa: E402


CONTENT_ROOT = Path(__file__).parents[1] / "src" / "usdquest" / "lessons" / "content"
M01 = CONTENT_ROOT / "act01_first_day" / "m01_hello_stage" / "mission.yaml"


GOLDEN_M01 = """#usda 1.0
(
    defaultPrim = "World"
)

def Xform "World"
{
    def Cube "Cube"
    {
    }
}
"""


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "player.usda"
    p.write_text(content, encoding="utf-8")
    return p


def test_m01_golden_passes(tmp_path: Path) -> None:
    mission = load_mission(M01)
    path = _write(tmp_path, GOLDEN_M01)
    report = grade(mission, path)
    assert report.passed, [r.message for r in report.results if not r.passed]
    assert report.earned_xp == 50


_MUT_NO_WORLD = "#usda 1.0\n"

_MUT_SCOPE_INSTEAD_OF_XFORM = """#usda 1.0
(
    defaultPrim = "World"
)
def Scope "World"
{
    def Cube "Cube"
    {
    }
}
"""

_MUT_NO_CUBE = """#usda 1.0
(
    defaultPrim = "World"
)
def Xform "World"
{
}
"""

_MUT_NO_DEFAULT_PRIM = """#usda 1.0
def Xform "World"
{
    def Cube "Cube"
    {
    }
}
"""


@pytest.mark.parametrize(
    "mutation,expected_failing_objective",
    [
        (_MUT_NO_WORLD, "world_xform_exists"),
        (_MUT_SCOPE_INSTEAD_OF_XFORM, "world_xform_exists"),
        (_MUT_NO_CUBE, "cube_exists"),
        (_MUT_NO_DEFAULT_PRIM, "default_prim_set"),
    ],
)
def test_m01_rejects_bad_mutations(
    tmp_path: Path, mutation: str, expected_failing_objective: str
) -> None:
    mission = load_mission(M01)
    path = _write(tmp_path, mutation)
    report = grade(mission, path)
    assert not report.passed
    failing = {r.objective.id for r in report.results if not r.passed}
    assert expected_failing_objective in failing, (
        f"expected {expected_failing_objective} to fail, got failures: {failing}"
    )
