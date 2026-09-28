import sys
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QRadialGradient, QLinearGradient, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget

class JellySphereWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Base sphere parameters
        self.base_radius = 170.0
        self.num_vertices = 96

        # Harmonic wave parameters for squishy jelly physics
        self.perturbations = [0.0] * self.num_vertices
        self.velocities = [0.0] * self.num_vertices
        self.stiffness = 0.16
        self.damping = 0.88
        self.coupling = 0.22

        # Core displacement
        self.core_dx = 0.0
        self.core_dy = 0.0
        self.core_vx = 0.0
        self.core_vy = 0.0

        # Mouse tracking
        self.mouse_pos = QPointF(-1000, -1000)
        self.prev_mouse = QPointF(-1000, -1000)
        self.time_counter = 0.0

        # 60 FPS update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(16)

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position()

    def update_simulation(self):
        self.time_counter += 0.03
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0

        # Mouse impulse calculation
        mx = self.mouse_pos.x() - center_x
        my = self.mouse_pos.y() - center_y
        m_dist = math.hypot(mx, my)

        m_vx = self.mouse_pos.x() - self.prev_mouse.x() if self.prev_mouse.x() > -900 else 0
        m_vy = self.mouse_pos.y() - self.prev_mouse.y() if self.prev_mouse.y() > -900 else 0
        m_speed = math.hypot(m_vx, m_vy)
        self.prev_mouse = QPointF(self.mouse_pos)

        # When cursor nears or touches the sphere
        if m_dist < self.base_radius + 60:
            mouse_angle = math.atan2(my, mx)
            if mouse_angle < 0:
                mouse_angle += 2 * math.pi

            push = max(0.0, (self.base_radius + 40 - m_dist) * 0.45) + min(18.0, m_speed * 0.35)

            # Apply localized impulse across neighboring boundary vertices
            for i in range(self.num_vertices):
                theta = (2 * math.pi * i) / self.num_vertices
                diff = abs(theta - mouse_angle)
                if diff > math.pi:
                    diff = 2 * math.pi - diff

                if diff < 0.65:
                    env = math.cos((diff / 0.65) * (math.pi / 2))
                    self.velocities[i] -= push * env * 0.4

            # Shift the core center toward mouse motion
            self.core_vx += (mx / max(1.0, m_dist)) * (push * 0.08)
            self.core_vy += (my / max(1.0, m_dist)) * (push * 0.08)

        # Update spring physics with neighbor coupling (tension)
        new_velocities = list(self.velocities)
        for i in range(self.num_vertices):
            left = (i - 1) % self.num_vertices
            right = (i + 1) % self.num_vertices

            restoring = -self.stiffness * self.perturbations[i]
            neighbor_pull = self.coupling * (self.perturbations[left] + self.perturbations[right] - 2 * self.perturbations[i])
            
            new_velocities[i] = (new_velocities[i] + restoring + neighbor_pull) * self.damping
            self.perturbations[i] += new_velocities[i]

        self.velocities = new_velocities

        # Core spring-back physics
        self.core_vx = (self.core_vx - 0.12 * self.core_dx) * 0.90
        self.core_vy = (self.core_vy - 0.12 * self.core_dy) * 0.90
        self.core_dx += self.core_vx
        self.core_dy += self.core_vy

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0
        cy = h / 2.0

        # 1. Deep Space Cyber Background
        bg_grad = QRadialGradient(cx, cy, max(w, h) * 0.7, cx, cy)
        bg_grad.setColorAt(0.0, QColor(14, 20, 32))
        bg_grad.setColorAt(0.6, QColor(7, 10, 16))
        bg_grad.setColorAt(1.0, QColor(3, 4, 7))
        painter.fillRect(self.rect(), bg_grad)

        # 2. Ambient Underglow Halo behind sphere
        glow_grad = QRadialGradient(cx + self.core_dx * 0.5, cy + self.core_dy * 0.5, self.base_radius * 1.55)
        glow_grad.setColorAt(0.0, QColor(0, 229, 255, 60))
        glow_grad.setColorAt(0.5, QColor(0, 140, 255, 20))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx + self.core_dx * 0.5, cy + self.core_dy * 0.5), self.base_radius * 1.5, self.base_radius * 1.5)

        # 3. Construct Smooth Deformed Polygon Path
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        points = []
        for i in range(self.num_vertices):
            theta = (2 * math.pi * i) / self.num_vertices
            r = self.base_radius + self.perturbations[i]
            px = cx + self.core_dx + r * math.cos(theta)
            py = cy + self.core_dy + r * math.sin(theta)
            points.append(QPointF(px, py))

        path.moveTo(points[0])
        for i in range(self.num_vertices):
            p_next = points[(i + 1) % self.num_vertices]
            mid_pt = QPointF((points[i].x() + p_next.x()) / 2.0, (points[i].y() + p_next.y()) / 2.0)
            path.quadTo(points[i], mid_pt)
        path.closeSubpath()

        # 4. Volumetric Sphere Shading (Diffuse 3D Radial Core)
        light_x = cx + self.core_dx - self.base_radius * 0.38
        light_y = cy + self.core_dy - self.base_radius * 0.42
        sphere_grad = QRadialGradient(light_x, light_y, self.base_radius * 1.35)
        sphere_grad.setColorAt(0.0, QColor(140, 245, 255))
        sphere_grad.setColorAt(0.2, QColor(0, 200, 255))
        sphere_grad.setColorAt(0.55, QColor(0, 100, 210))
        sphere_grad.setColorAt(0.85, QColor(5, 40, 95))
        sphere_grad.setColorAt(1.0, QColor(2, 16, 42))

        painter.setBrush(QBrush(sphere_grad))
        painter.setPen(QPen(QColor(0, 255, 255, 180), 2.0))
        painter.drawPath(path)

        # 5. Inner Glass Reflection / Specular Sheen (Top Left)
        spec_x = cx + self.core_dx - self.base_radius * 0.35
        spec_y = cy + self.core_dy - self.base_radius * 0.40
        spec_grad = QRadialGradient(spec_x, spec_y, self.base_radius * 0.45)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        spec_grad.setColorAt(0.3, QColor(180, 240, 255, 140))
        spec_grad.setColorAt(0.8, QColor(0, 200, 255, 0))
        painter.setBrush(QBrush(spec_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(spec_x, spec_y), self.base_radius * 0.32, self.base_radius * 0.22)

        # 6. Secondary Soft Rim Fresnel (Bottom Right)
        rim_x = cx + self.core_dx + self.base_radius * 0.42
        rim_y = cy + self.core_dy + self.base_radius * 0.42
        rim_grad = QRadialGradient(rim_x, rim_y, self.base_radius * 0.6)
        rim_grad.setColorAt(0.0, QColor(0, 255, 200, 80))
        rim_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rim_grad))
        painter.drawEllipse(QPointF(rim_x, rim_y), self.base_radius * 0.45, self.base_radius * 0.35)

        # 7. Subdued UI Telemetry
        painter.setPen(QColor(139, 148, 158, 120))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(24, 32, "VOLUMETRIC ELASTIC SPHERE // 60 FPS")
        painter.drawText(24, 48, "INTERACTION: Move cursor over or slice through to trigger jiggle waves")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Volumetric Jelly Sphere")
        self.resize(880, 680)
        self.setCentralWidget(JellySphereWidget(self))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
