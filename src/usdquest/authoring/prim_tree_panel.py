"""Read-only prim-hierarchy tree for the current stage."""
from __future__ import annotations

from PySide6 import QtWidgets

from pxr import Usd


class PrimTreePanel(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setHeaderLabels(["Prim", "Type"])

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QLabel("Prim Hierarchy", self))
        layout.addWidget(self._tree, 1)

    def refresh(self, stage: Usd.Stage | None) -> None:
        self._tree.clear()
        if stage is None:
            return
        root = stage.GetPseudoRoot()
        for child in root.GetChildren():
            self._tree.addTopLevelItem(self._build(child))
        self._tree.expandAll()
        self._tree.resizeColumnToContents(0)

    @staticmethod
    def _build(prim: Usd.Prim) -> QtWidgets.QTreeWidgetItem:
        item = QtWidgets.QTreeWidgetItem([prim.GetName(), prim.GetTypeName() or "(unspecified)"])
        for child in prim.GetChildren():
            item.addChild(PrimTreePanel._build(child))
        return item
