import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget


class AICoreVisualization(QWidget):
    """
    Animated JARVIS Arc Reactor / AI Core visualization component.
    Displays dynamic rotating glowing rings and pulsing core according to state:
    idle, thinking, speaking, error.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)

        self.state = "idle"  # idle, thinking, speaking, error
        self.angle = 0.0
        self.pulse_phase = 0.0

        # Animation update timer (~60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(16)

    def set_state(self, new_state: str):
        """Updates the state of the AI core visualization."""
        if self.state != new_state:
            self.state = str(new_state).lower()
            self.update()

    def _update_animation(self):
        """Advances animation counters."""
        if self.state == "thinking":
            self.angle = (self.angle + 4.0) % 360.0
            self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        elif self.state == "speaking":
            self.angle = (self.angle + 2.5) % 360.0
            self.pulse_phase = (self.pulse_phase + 0.15) % (2 * math.pi)
        elif self.state == "error":
            self.angle = (self.angle + 1.0) % 360.0
            self.pulse_phase = (self.pulse_phase + 0.05) % (2 * math.pi)
        else:  # idle
            self.angle = (self.angle + 0.8) % 360.0
            self.pulse_phase = (self.pulse_phase + 0.03) % (2 * math.pi)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2.0
        center_y = height / 2.0
        radius = min(width, height) / 2.0 - 15.0

        # State color schemes
        if self.state == "thinking":
            primary_color = QColor(0, 220, 255)
            secondary_color = QColor(0, 150, 255)
            status_text = "THINKING..."
        elif self.state == "speaking":
            primary_color = QColor(127, 255, 212)  # Aquamarine
            secondary_color = QColor(0, 230, 180)
            status_text = "SPEAKING..."
        elif self.state == "error":
            primary_color = QColor(255, 80, 80)
            secondary_color = QColor(200, 40, 40)
            status_text = "ERROR"
        else:  # idle
            primary_color = QColor(0, 180, 240)
            secondary_color = QColor(0, 100, 200)
            status_text = "JARVIS ONLINE"

        # Outer ring
        pen = QPen(primary_color, 2)
        painter.setPen(pen)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Rotating segmented ring
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)

        num_segments = 12
        segment_radius = radius - 10.0
        for i in range(num_segments):
            angle_deg = i * (360.0 / num_segments)
            painter.save()
            painter.rotate(angle_deg)
            pen = QPen(secondary_color, 3 if i % 2 == 0 else 1.5)
            painter.setPen(pen)
            painter.drawLine(int(segment_radius - 8), 0, int(segment_radius), 0)
            painter.restore()

        # Counter-rotating inner ring
        painter.rotate(-self.angle * 2)
        inner_radius = radius - 25.0
        pen = QPen(primary_color, 1.5, Qt.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(-inner_radius, -inner_radius, inner_radius * 2, inner_radius * 2)

        painter.restore()

        # Pulsing center core
        pulse = (math.sin(self.pulse_phase) + 1.0) / 2.0  # 0.0 to 1.0
        core_radius = (radius - 40.0) + (pulse * 6.0)

        core_gradient = QLinearGradient(center_x, center_y - core_radius, center_x, center_y + core_radius)
        core_color = QColor(primary_color)
        core_color.setAlpha(int(150 + pulse * 80))
        core_gradient.setColorAt(0.0, core_color)
        glow_color = QColor(primary_color)
        glow_color.setAlpha(40)
        core_gradient.setColorAt(1.0, glow_color)

        painter.setBrush(core_gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - core_radius, center_y - core_radius, core_radius * 2, core_radius * 2)

        # Core center label
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor(240, 245, 255))
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            status_text
        )
