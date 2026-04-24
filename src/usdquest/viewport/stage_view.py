"""Embeds pxr.Usdviewq.StageView as a PySide6 widget.

StageView is the same Hydra-backed viewport that powers Pixar's `usdview`. We reuse
its UsdviewDataModel (selection, viewer settings) and StageView widget directly —
the narrative shell in USD Quest skins around it, it does not replace it.
"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtWidgets

from pxr import Usd
from pxr.Usdviewq.appController import UsdviewDataModel
from pxr.Usdviewq.common import Timer
from pxr.Usdviewq.settings import Settings
from pxr.Usdviewq.stageView import StageView


_SETTINGS_VERSION = "usdquest-0"


class USDQuestStageView(QtWidgets.QWidget):
    """Container widget that owns a Usd.Stage and a Usdviewq.StageView."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        # Ephemeral (no file) so we don't spam the user's disk in M0.
        self._settings = Settings(_SETTINGS_VERSION, stateFilePath=None)
        self._data_model = UsdviewDataModel(makeTimer=Timer, settings=self._settings)

        self._stage_view = StageView(dataModel=self._data_model, parent=self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stage_view)

    def load_stage(self, path: str | Path) -> Usd.Stage:
        stage = Usd.Stage.Open(str(path))
        if stage is None:
            raise RuntimeError(f"Failed to open stage: {path}")
        self._data_model.stage = stage
        self._stage_view.setUpdatesEnabled(True)
        self._stage_view.updateView(resetCam=True, forceComputeBBox=True)
        return stage

    @property
    def stage(self) -> Usd.Stage | None:
        return self._data_model.stage

    @property
    def data_model(self) -> UsdviewDataModel:
        return self._data_model
