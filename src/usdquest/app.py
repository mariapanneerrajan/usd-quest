"""USD Quest — entry point.

M1 scope: one scripted mission runs end-to-end. The player edits a .usda file
in a built-in editor, saves, the app reloads the stage into the Hydra viewport,
and clicking "Grade" runs the mission's objective checks.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

# Bootstrap USD before importing anything that touches pxr.
from usdquest.packaging.usd_bootstrap import bootstrap, resolved_root

bootstrap()

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from usdquest.authoring.layer_stack_panel import LayerStackPanel  # noqa: E402
from usdquest.authoring.mission_panel import MissionPanel  # noqa: E402
from usdquest.authoring.prim_tree_panel import PrimTreePanel  # noqa: E402
from usdquest.authoring.usda_editor import UsdaEditor  # noqa: E402
from usdquest.lessons.grader import grade  # noqa: E402
from usdquest.lessons.mission import Mission, load_mission  # noqa: E402
from usdquest.progress.save import ProgressStore, default_db_path  # noqa: E402
from usdquest.viewport.stage_view import USDQuestStageView  # noqa: E402


CONTENT_ROOT = Path(__file__).parent / "lessons" / "content"
FIRST_MISSION = CONTENT_ROOT / "act01_first_day" / "m01_hello_stage" / "mission.yaml"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, mission: Mission, workspace: Path, store: ProgressStore) -> None:
        super().__init__()
        self.setWindowTitle(f"USD Quest — {mission.title}")
        self.resize(1600, 980)

        self._mission = mission
        self._workspace = workspace
        self._store = store

        # Prepare player's working file from starter (or blank) on first entry.
        self._player_path = workspace / mission.target_stage
        if not self._player_path.exists():
            if mission.starter_path and mission.starter_path.exists():
                shutil.copy(mission.starter_path, self._player_path)
            else:
                self._player_path.write_text("#usda 1.0\n", encoding="utf-8")

        # Widgets
        self.viewport = USDQuestStageView(self)
        self.editor = UsdaEditor(self)
        self.mission_panel = MissionPanel(self)
        self.layer_panel = LayerStackPanel(self)
        self.prim_panel = PrimTreePanel(self)

        self.editor.load_file(self._player_path)
        self.mission_panel.set_mission(mission)
        self.editor.saved.connect(self._on_saved)
        self.mission_panel.grade_requested.connect(self._on_grade_clicked)

        # Layout: left = mission + layer/prim tree; center = viewport over editor
        left_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        left_split.addWidget(self.mission_panel)
        left_tabs = QtWidgets.QTabWidget()
        left_tabs.addTab(self.prim_panel, "Prims")
        left_tabs.addTab(self.layer_panel, "Layers")
        left_split.addWidget(left_tabs)
        left_split.setStretchFactor(0, 1)
        left_split.setStretchFactor(1, 2)

        center_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        center_split.addWidget(self.viewport)
        center_split.addWidget(self.editor)
        center_split.setStretchFactor(0, 3)
        center_split.setStretchFactor(1, 2)

        root_split = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        root_split.addWidget(left_split)
        root_split.addWidget(center_split)
        root_split.setStretchFactor(0, 1)
        root_split.setStretchFactor(1, 3)

        self.setCentralWidget(root_split)
        self.statusBar().showMessage(
            f"USD: {resolved_root()}  |  XP: {store.total_xp()}  |  Workspace: {workspace}"
        )

        # First load.
        self._reload_stage()

    # --- slots ---
    def _on_saved(self, path: Path) -> None:
        self._reload_stage()

    def _on_grade_clicked(self) -> None:
        # Make sure latest edits are on disk before grading.
        self.editor.save()
        report = grade(self._mission, self._player_path)
        self.mission_panel.show_report(report)
        if report.passed and not self._store.is_complete(self._mission.id):
            self._store.record_completion(self._mission.id, report.earned_xp)
            self.statusBar().showMessage(
                f"Mission complete! XP: {self._store.total_xp()}"
            )

    # --- helpers ---
    def _reload_stage(self) -> None:
        try:
            stage = self.viewport.load_stage(self._player_path)
        except Exception as e:
            self.statusBar().showMessage(f"Stage load error: {e}")
            return
        self.layer_panel.refresh(stage)
        self.prim_panel.refresh(stage)


def main() -> int:
    mission = load_mission(FIRST_MISSION)

    # Per-mission workspace so we don't mutate the shipped starter.
    data_root = Path(
        (
            # env override -> else local app data -> else temp
            (lambda: __import__("os").environ.get("USDQUEST_DATA_DIR"))()
            or (lambda: __import__("os").environ.get("LOCALAPPDATA"))()
            or tempfile.gettempdir()
        )
    )
    workspace = data_root / "USDQuest" / "workspace" / mission.id
    workspace.mkdir(parents=True, exist_ok=True)

    store = ProgressStore(default_db_path())

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(mission, workspace, store)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
