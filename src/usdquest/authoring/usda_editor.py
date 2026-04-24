"""A plain-text editor panel for a single .usda file.

Save-on-demand (Ctrl+S or the toolbar button) so the grader always acts on
what's been written to disk, not on in-memory buffer state.
"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


class UsdaEditor(QtWidgets.QWidget):
    saved = QtCore.Signal(Path)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._path: Path | None = None

        self._editor = QtWidgets.QPlainTextEdit(self)
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        font.setPointSize(10)
        self._editor.setFont(font)
        self._editor.setTabStopDistance(4 * self._editor.fontMetrics().horizontalAdvance(" "))

        self._path_label = QtWidgets.QLabel("(no file)", self)
        self._save_button = QtWidgets.QPushButton("Save (Ctrl+S)", self)
        self._save_button.clicked.connect(self.save)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self._path_label, 1)
        top.addWidget(self._save_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(top)
        layout.addWidget(self._editor, 1)

        shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Save, self)
        shortcut.activated.connect(self.save)

    def load_file(self, path: Path) -> None:
        self._path = path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        self._editor.setPlainText(text)
        self._path_label.setText(str(path))

    def save(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._editor.toPlainText(), encoding="utf-8")
        self.saved.emit(self._path)

    @property
    def path(self) -> Path | None:
        return self._path
