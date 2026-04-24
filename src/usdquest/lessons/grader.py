"""Runs a mission's objective checks against a Usd.Stage.

Each objective's `check` is a snippet of Python. The grader exec()s it with a
restricted globals dict exposing `stage`, `Usd`, `Sdf`, `Pcp`, `Ar`, `UsdGeom`,
`UsdShade`, `UsdLux`, and the mission's root_layer_path. An `AssertionError`
(or any exception) means the objective failed; clean return means pass.

This is NOT a security sandbox — the player is running their own machine's
Python. It is a *scoping* sandbox: it gives mission authors a simple, consistent
surface to write checks against.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path

from pxr import Ar, Pcp, Sdf, Usd, UsdGeom, UsdLux, UsdShade

from usdquest.lessons.mission import Mission, Objective


@dataclass(frozen=True)
class ObjectiveResult:
    objective: Objective
    passed: bool
    message: str  # "" on pass, assertion/error text on fail


@dataclass(frozen=True)
class GradeReport:
    mission: Mission
    results: tuple[ObjectiveResult, ...]

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def earned_xp(self) -> int:
        return self.mission.reward.xp if self.passed else 0


def grade(mission: Mission, target_path: Path | None = None) -> GradeReport:
    """Open the player's authored stage and run every objective check."""
    root = target_path or mission.target_path
    if not root.exists():
        missing = ObjectiveResult(
            objective=Objective("stage_exists", "Stage file exists", ""),
            passed=False,
            message=f"No stage found at {root}",
        )
        return GradeReport(mission=mission, results=(missing,))

    # USD caches Sdf.Layer by identifier, so if another part of the app already
    # opened this file, Open() will return the stale cached content. Force a
    # reload so the grader always sees what's actually on disk.
    try:
        existing = Sdf.Layer.Find(str(root))
        if existing is not None:
            existing.Reload(force=True)
        stage = Usd.Stage.Open(str(root))
    except Exception as e:
        fail = ObjectiveResult(
            objective=Objective("stage_opens", "Stage is a valid USD file", ""),
            passed=False,
            message=f"Usd.Stage.Open raised: {e}",
        )
        return GradeReport(mission=mission, results=(fail,))
    if stage is None:
        fail = ObjectiveResult(
            objective=Objective("stage_opens", "Stage is a valid USD file", ""),
            passed=False,
            message=f"Usd.Stage.Open returned None for {root}",
        )
        return GradeReport(mission=mission, results=(fail,))

    results: list[ObjectiveResult] = []
    for obj in mission.objectives:
        result = _run_check(obj, stage, root)
        results.append(result)

    return GradeReport(mission=mission, results=tuple(results))


def _run_check(obj: Objective, stage: Usd.Stage, root_layer_path: Path) -> ObjectiveResult:
    globs: dict = {
        "stage": stage,
        "root_layer_path": str(root_layer_path),
        "Usd": Usd,
        "Sdf": Sdf,
        "Pcp": Pcp,
        "Ar": Ar,
        "UsdGeom": UsdGeom,
        "UsdShade": UsdShade,
        "UsdLux": UsdLux,
    }
    try:
        exec(compile(obj.check, f"<mission:{obj.id}>", "exec"), globs)
    except AssertionError as e:
        return ObjectiveResult(obj, passed=False, message=str(e) or "assertion failed")
    except Exception as e:
        tb = traceback.format_exception_only(type(e), e)[-1].strip()
        return ObjectiveResult(obj, passed=False, message=tb)
    return ObjectiveResult(obj, passed=True, message="")
