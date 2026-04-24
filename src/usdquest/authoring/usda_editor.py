"""A plain-text editor panel for a single .usda file.

Shows a clear dirty/saved indicator so the player always knows whether their
buffer matches what's on disk. Save-on-demand (Ctrl+S or the toolbar button);
the grader always reads from disk, not the buffer.
"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


_STATUS_CLEAN = "Saved"
_STATUS_DIRTY = "Unsaved changes"
_STATUS_JUST_SAVED = "Saved just now"

_CLEAN_CSS = "color: #2a7; font-weight: bold;"
_DIRTY_CSS = "color: #c60; font-weight: bold;"
_FLASH_CSS = "color: #2a7; font-weight: bold; background-color: #e7f7e7; padding: 1px 6px; border-radius: 3px;"


class UsdaEditor(QtWidgets.QWidget):
    saved = QtCore.Signal(Path)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._path: Path | None = None
        self._on_disk_text: str = ""

        self._editor = QtWidgets.QPlainTextEdit(self)
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        font.setPointSize(10)
        self._editor.setFont(font)
        self._editor.setTabStopDistance(4 * self._editor.fontMetrics().horizontalAdvance(" "))
        self._editor.textChanged.connect(self._on_text_changed)

        self._path_label = QtWidgets.QLabel("(no file)", self)
        self._status_label = QtWidgets.QLabel(_STATUS_CLEAN, self)
        self._status_label.setStyleSheet(_CLEAN_CSS)

        self._save_button = QtWidgets.QPushButton("Save (Ctrl+S)", self)
        self._save_button.clicked.connect(self.save)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self._path_label, 1)
        top.addWidget(self._status_label)
        top.addWidget(self._save_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(top)
        layout.addWidget(self._editor, 1)

        shortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Save, self)
        shortcut.activated.connect(self.save)

        self._flash_timer = QtCore.QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._end_flash)

    # ---- public API ----
    def load_file(self, path: Path) -> None:
        self._path = path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        self._on_disk_text = text
        # Block signals so loading doesn't mark the buffer dirty.
        self._editor.blockSignals(True)
        self._editor.setPlainText(text)
        self._editor.blockSignals(False)
        self._path_label.setText(str(path))
        self._set_clean()

    def save(self) -> None:
        if self._path is None:
            return
        if not self.is_dirty():
            # No-op but still give the user positive feedback.
            self._flash_saved()
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        text = self._editor.toPlainText()
        self._path.write_text(text, encoding="utf-8")
        self._on_disk_text = text
        self._set_clean()
        self._flash_saved()
        self.saved.emit(self._path)

    def is_dirty(self) -> bool:
        if self._path is None:
            return False
        return self._editor.toPlainText() != self._on_disk_text

    @property
    def path(self) -> Path | None:
        return self._path

    # ---- internal ----
    def _on_text_changed(self) -> None:
        if self.is_dirty():
            self._status_label.setText(_STATUS_DIRTY + " •")
            self._status_label.setStyleSheet(_DIRTY_CSS)
            self._save_button.setText("Save* (Ctrl+S)")
        else:
            self._set_clean()

    def _set_clean(self) -> None:
        self._status_label.setText(_STATUS_CLEAN)
        self._status_label.setStyleSheet(_CLEAN_CSS)
        self._save_button.setText("Save (Ctrl+S)")

    def _flash_saved(self) -> None:
        self._status_label.setText(_STATUS_JUST_SAVED)
        self._status_label.setStyleSheet(_FLASH_CSS)
        self._flash_timer.start(1500)

    def _end_flash(self) -> None:
        # After the flash, revert to whatever state the buffer is currently in.
        if self.is_dirty():
            self._on_text_changed()
        else:
            self._set_clean()
