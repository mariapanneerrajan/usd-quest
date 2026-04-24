"""Mission briefing panel: story, objective checklist, grade button, results."""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from usdquest.lessons.grader import GradeReport
from usdquest.lessons.mission import Mission


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

        self._story = QtWidgets.QLabel("", self)
        self._story.setWordWrap(True)
        self._story.setStyleSheet("color: #666;")

        self._objectives = QtWidgets.QTreeWidget(self)
        self._objectives.setHeaderLabels(["Objective", "Status"])
        self._objectives.setRootIsDecorated(False)

        self._grade_button = QtWidgets.QPushButton("Grade mission", self)
        self._grade_button.clicked.connect(self.grade_requested)

        self._summary = QtWidgets.QLabel("", self)
        self._summary.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._story)
        layout.addWidget(self._objectives, 1)
        layout.addWidget(self._grade_button)
        layout.addWidget(self._summary)

    def set_mission(self, mission: Mission) -> None:
        self._mission = mission
        self._title.setText(f"Act {mission.act} — {mission.title}")
        self._story.setText(mission.story)
        self._objectives.clear()
        for obj in mission.objectives:
            item = QtWidgets.QTreeWidgetItem([obj.description, "—"])
            self._objectives.addTopLevelItem(item)
        self._objectives.resizeColumnToContents(0)
        self._summary.setText("")

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
