"""Mission format + loader.

A mission is a YAML file describing a single graded USD task. Each mission ships
with (optionally) a starter stage file; the grader opens whatever the player has
authored and runs declared objective checks against it.

YAML schema:

    id: act1_m01_hello_stage
    act: 1
    title: "Hello, Stage"
    story: |
      Your first day at the studio. Open a fresh stage and put
      a single cube at the origin under /World.
    starter_stage: starter.usda   # optional, relative to the mission dir
    target_stage: player.usda     # required, relative to the mission dir
    objectives:
      - id: world_xform_exists
        description: "/World is defined as an Xform"
        check: |
          prim = stage.GetPrimAtPath("/World")
          assert prim and prim.IsValid(), "No /World prim"
          assert prim.GetTypeName() == "Xform", "/World must be an Xform"
      - id: cube_exists
        description: "/World/Cube is a Cube at the origin"
        check: |
          prim = stage.GetPrimAtPath("/World/Cube")
          assert prim and prim.IsValid(), "No /World/Cube prim"
          assert prim.GetTypeName() == "Cube", "/World/Cube must be a Cube"
    reward:
      xp: 50
      badge: first_stage
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Objective:
    id: str
    description: str
    check: str  # python source, executed by Grader


@dataclass(frozen=True)
class Reward:
    xp: int = 0
    badge: str | None = None


@dataclass(frozen=True)
class Mission:
    id: str
    act: int
    title: str
    story: str
    mission_dir: Path
    objectives: tuple[Objective, ...]
    reward: Reward = field(default_factory=Reward)
    starter_stage: str | None = None
    target_stage: str = "player.usda"

    @property
    def target_path(self) -> Path:
        return self.mission_dir / self.target_stage

    @property
    def starter_path(self) -> Path | None:
        if self.starter_stage is None:
            return None
        return self.mission_dir / self.starter_stage


def load_mission(mission_yaml: Path) -> Mission:
    data: dict[str, Any] = yaml.safe_load(mission_yaml.read_text(encoding="utf-8"))
    mission_dir = mission_yaml.parent

    objectives = tuple(
        Objective(id=o["id"], description=o["description"], check=o["check"])
        for o in data.get("objectives", [])
    )
    reward_data = data.get("reward", {}) or {}
    reward = Reward(xp=int(reward_data.get("xp", 0)), badge=reward_data.get("badge"))

    return Mission(
        id=data["id"],
        act=int(data["act"]),
        title=data["title"],
        story=data.get("story", "").strip(),
        mission_dir=mission_dir,
        objectives=objectives,
        reward=reward,
        starter_stage=data.get("starter_stage"),
        target_stage=data.get("target_stage", "player.usda"),
    )
