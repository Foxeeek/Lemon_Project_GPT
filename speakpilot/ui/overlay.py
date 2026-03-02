"""PyQt6 floating overlay window for correction output."""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QTimer, Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class OverlayWindow(QWidget):
    """Always-on-top translucent overlay showing correction details and summaries."""

    def __init__(self, interview_mode: bool = False) -> None:
        super().__init__()
        self._drag_origin: QPoint | None = None
        self._interview_mode = interview_mode

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        container = QWidget(self)
        container.setObjectName("container")

        self._badge_label = QLabel()
        self._badge_label.setText("INTERVIEW MODE" if interview_mode else "LIVE MODE")
        self._badge_label.setStyleSheet(
            "color: rgba(255,255,255,0.9); font-size: 11px; font-weight: 700; "
            "letter-spacing: 0.8px;"
        )

        self._original_label = QLabel()
        self._original_label.setTextFormat(Qt.TextFormat.RichText)
        self._original_label.setWordWrap(True)
        self._original_label.setStyleSheet("color: rgba(230, 230, 230, 0.72); font-size: 14px;")

        self._corrected_label = QLabel()
        self._corrected_label.setTextFormat(Qt.TextFormat.RichText)
        self._corrected_label.setWordWrap(True)
        self._corrected_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 600;")

        self._explanation_label = QLabel()
        self._explanation_label.setTextFormat(Qt.TextFormat.RichText)
        self._explanation_label.setWordWrap(True)
        self._explanation_label.setStyleSheet("color: rgba(210, 210, 210, 0.85); font-size: 12px;")

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(14, 12, 14, 12)
        inner_layout.setSpacing(8)
        inner_layout.addWidget(self._badge_label)
        inner_layout.addWidget(self._original_label)
        inner_layout.addWidget(self._corrected_label)
        inner_layout.addWidget(self._explanation_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        self.setStyleSheet(
            """
            QWidget#container {
                background-color: rgba(20, 20, 24, 190);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 35);
            }
            """
        )

        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(200)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        self.resize(520, 220)
        self.setMaximumHeight(280)

    def show_correction(self, original: str, corrected_html: str, explanation: str) -> None:
        """Update overlay contents and resize to fit text."""
        self._badge_label.setText("INTERVIEW MODE" if self._interview_mode else "LIVE MODE")
        self._original_label.setText(f"<span>Original: {original}</span>")
        self._corrected_label.setText(f"<span>Corrected: {corrected_html}</span>")
        self._explanation_label.setText(f"<span>Explanation: {explanation}</span>")
        self._show_with_fade()

    def show_summary(self, summary_text: str) -> None:
        """Show end-of-session summary in the overlay."""
        self._badge_label.setText("INTERVIEW SUMMARY" if self._interview_mode else "SESSION SUMMARY")
        self._original_label.setText("")
        self._corrected_label.setText(f"<span>{summary_text}</span>")
        self._explanation_label.setText("")
        self._show_with_fade()

    def _show_with_fade(self) -> None:
        self.adjustSize()
        if self.height() > self.maximumHeight():
            self.resize(self.width(), self.maximumHeight())
        self.setWindowOpacity(0.0)
        self.show()
        self._fade.stop()
        self._fade.start()
        self._hide_timer.start(6000)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_origin = None
        event.accept()
