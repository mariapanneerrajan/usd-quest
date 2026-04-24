"""Mission briefing panel: story, objective checklist, grade button, results."""
from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from usdquest.lessons.grader import GradeReport
from usdquest.lessons.mission import Mission


_SELECTABLE = (
    QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
    | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
    | QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
    | QtCore.Qt.TextInteractionFlag.LinksAccessibleByKeyboard
)


class MissionPanel(QtWidgets.QWidget):
    grade_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._mission: Mission | None = None

        self._title = QtWidgets.QLabel("(no mission loaded)", self)
        title_font = self._title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        self._title.setFont(title_font)
        self._title.setTextInteractionFlags(_SELECTABLE)
        self._title.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.IBeamCursor))

        self._story = QtWidgets.QLabel("", self)
        self._story.setWordWrap(True)
        self._story.setStyleSheet("color: #666;")
        self._story.setTextInteractionFlags(_SELECTABLE)
        self._story.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.IBeamCursor))
        self._story.setOpenExternalLinks(True)

        self._lesson = QtWidgets.QTextBrowser(self)
        self._lesson.setOpenExternalLinks(True)
        self._lesson.setMinimumHeight(140)
        self._lesson.setVisible(False)

        self._objectives = QtWidgets.QTreeWidget(self)
        self._objectives.setHeaderLabels(["Objective", "Status"])
        self._objectives.setRootIsDecorated(False)

        self._grade_button = QtWidgets.QPushButton("Grade mission", self)
        self._grade_button.clicked.connect(self.grade_requested)

        self._summary = QtWidgets.QLabel("", self)
        self._summary.setWordWrap(True)
        self._summary.setTextInteractionFlags(_SELECTABLE)
        self._summary.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.IBeamCursor))

        self._hint_button = QtWidgets.QPushButton("Show a hint", self)
        self._hint_button.clicked.connect(self._show_next_hint)
        self._hints_shown = 0

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._story)
        layout.addWidget(self._lesson)
        layout.addWidget(self._objectives, 1)
        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self._hint_button)
        button_row.addWidget(self._grade_button)
        layout.addLayout(button_row)
        layout.addWidget(self._summary)

    def set_mission(self, mission: Mission) -> None:
        self._mission = mission
        self._title.setText(f"Act {mission.act} — {mission.title}")
        self._story.setText(mission.story)

        if mission.lesson:
            self._lesson.setMarkdown(mission.lesson)
            self._lesson.setVisible(True)
        else:
            self._lesson.setVisible(False)

        self._objectives.clear()
        for obj in mission.objectives:
            item = QtWidgets.QTreeWidgetItem([obj.description, "—"])
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsSelectable)
            self._objectives.addTopLevelItem(item)
        self._objectives.resizeColumnToContents(0)
        self._summary.setText("")

        self._hints_shown = 0
        self._refresh_hint_button()

    def _refresh_hint_button(self) -> None:
        if self._mission is None or not self._mission.hints:
            self._hint_button.setVisible(False)
            return
        remaining = len(self._mission.hints) - self._hints_shown
        if remaining <= 0:
            self._hint_button.setText("All hints shown")
            self._hint_button.setEnabled(False)
        else:
            self._hint_button.setText(f"Show hint ({remaining} left)")
            self._hint_button.setEnabled(True)
        self._hint_button.setVisible(True)

    def _show_next_hint(self) -> None:
        if self._mission is None:
            return
        if self._hints_shown >= len(self._mission.hints):
            return
        hint = self._mission.hints[self._hints_shown]
        self._hints_shown += 1
        self._refresh_hint_button()
        # Append to the summary area as a persistent, selectable hint.
        existing = self._summary.text()
        header = f"<b>Hint {self._hints_shown}:</b> "
        self._summary.setText((existing + "<br>" if existing else "") + header + hint)

    def show_report(self, report: GradeReport) -> None:
        for i, result in enumerate(report.results):
            item = self._objectives.topLevelItem(i)
            if item is None:
                continue
            status = "PASS" if result.passed else f"FAIL — {result.message}"
            item.setText(1, status)
        if report.passed:
            self._summary.setText(
                f"<b style='color:#2a7'>All objectives passed.</b> +{report.earned_xp} XP."
            )
        else:
            failed = sum(1 for r in report.results if not r.passed)
            self._summary.setText(
                f"<b style='color:#c33'>{failed} objective(s) failed.</b> Read the FAIL notes and try again."
            )
