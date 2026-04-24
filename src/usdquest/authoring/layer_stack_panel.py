"""Read-only live layer-stack view for the current Usd.Stage.

Shows each layer in the stage's root layer stack, plus muted/dirty flags.
Future milestones will add reorder/mute controls; for M1 it's just a mirror
so the player can see how their authoring affects composition.
"""
from __future__ import annotations

from PySide6 import QtWidgets

from pxr import Usd


class LayerStackPanel(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setHeaderLabels(["Layer", "Dirty", "Muted"])
        self._tree.setRootIsDecorated(False)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QLabel("Layer Stack", self))
        layout.addWidget(self._tree, 1)

    def refresh(self, stage: Usd.Stage | None) -> None:
        self._tree.clear()
        if stage is None:
            return
        for layer in stage.GetLayerStack(includeSessionLayers=True):
            item = QtWidgets.QTreeWidgetItem(
                [
                    layer.identifier,
                    "yes" if layer.dirty else "",
                    "yes" if stage.IsLayerMuted(layer.identifier) else "",
                ]
            )
            self._tree.addTopLevelItem(item)
        self._tree.resizeColumnToContents(0)
