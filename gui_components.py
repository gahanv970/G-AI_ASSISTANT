from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QWidget


class LiquidGlassBackground(QWidget):
    """
    A futuristic liquid glass background container with a deep cyan/indigo gradient background.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Deep futuristic gradient background
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(10, 14, 26))
        gradient.setColorAt(0.5, QColor(15, 23, 42))
        gradient.setColorAt(1.0, QColor(8, 12, 20))

        painter.fillRect(self.rect(), gradient)


class LiquidGlassCard(QFrame):
    """
    A glassmorphism card component with translucent background and a glowing border.
    """

    def __init__(self, parent=None, corner_radius=20):
        super().__init__(parent)
        self.corner_radius = corner_radius
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)

        # Translucent glass fill
        glass_color = QColor(255, 255, 255, 15)
        painter.fillPath(path, QBrush(glass_color))

        # Subtle glowing glass border
        border_gradient = QLinearGradient(0, 0, self.width(), self.height())
        border_gradient.setColorAt(0.0, QColor(0, 200, 255, 90))
        border_gradient.setColorAt(0.5, QColor(255, 255, 255, 30))
        border_gradient.setColorAt(1.0, QColor(0, 200, 255, 60))

        pen = painter.pen()
        pen.setBrush(border_gradient)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawPath(path)
