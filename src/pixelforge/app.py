"""Pixel Forge — entry point. M0: load Kitchen_set.usd in an embedded StageView."""
from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap USD before importing anything that touches pxr.
from pixelforge.packaging.usd_bootstrap import bootstrap, resolved_root

bootstrap()

from PySide6 import QtWidgets  # noqa: E402

from pixelforge.viewport.stage_view import PixelForgeStageView  # noqa: E402


DEFAULT_STAGE = Path(r"C:\code\open_usd\assets\Kitchen_set\Kitchen_set.usd")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, stage_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("Pixel Forge — M0")
        self.resize(1280, 800)

        self.viewport = PixelForgeStageView(self)
        self.setCentralWidget(self.viewport)

        self.statusBar().showMessage(f"USD: {resolved_root()}  |  Stage: {stage_path}")
        self.viewport.load_stage(stage_path)


def main() -> int:
    stage_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_STAGE
    if not stage_path.exists():
        print(f"Stage not found: {stage_path}", file=sys.stderr)
        return 1

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(stage_path)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
