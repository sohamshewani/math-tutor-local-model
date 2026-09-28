import sys
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QRadialGradient, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget

class RealPhysicsSphere(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Baseline Geometry
        self.r0 = 165.0          # Equilibrium radius in pixels (meters scale)
        self.N = 120             # Surface mass elements
        self.d_theta = (2.0 * math.pi) / self.N

        # State Vectors (Position displacement and velocity for each node)
        self.dr = [0.0] * self.N
        self.v = [0.0] * self.N

        # Physical Constants
        self.dt = 1.0 / 60.0     # Time-step (seconds)
        self.k_hooke = 24.0      # Radial stiffness (Hooke's spring constant)
        self.gamma = 3.6         # Viscous air & internal damping
        self.tension = 8.5       # Surface tension (Young-Laplace coupling)
        self.k_contact = 38.0    # Hertzian contact stiffness
        self.c_contact = 2.2     # Contact damping factor

        # Rigid Body Center-of-Mass
        self.cm_x = 0.0
        self.cm_y = 0.0
        self.cm_vx = 0.0
        self.cm_vy = 0.0
        self.cm_k = 18.0
        self.cm_damping = 4.0

        # Cursor kinematic state
        self.mouse_pos = QPointF(-2000, -2000)
        self.prev_mouse = QPointF(-2000, -2000)
        self.mouse_v = QPointF(0, 0)

        # Physics loop (60 Hz fixed timestep)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step_physics)
        self.timer.start(16)

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position()

    def step_physics(self):
        cx = self.width() / 2.0 + self.cm_x
        cy = self.height() / 2.0 + self.cm_y

        # Track cursor velocity
        if self.prev_mouse.x() > -1000:
            self.mouse_v = (self.mouse_pos - self.prev_mouse) / self.dt
        else:
            self.mouse_v = QPointF(0, 0)
        self.prev_mouse = QPointF(self.mouse_pos)

        # Relative vector to cursor from ball center
        mx = self.mouse_pos.x() - cx
        my = self.mouse_pos.y() - cy
        d_mouse = math.hypot(mx, my)

        # 1. Contact Mechanics & Hertzian Impact
        cursor_radius = 14.0  # Virtual cursor contact sphere
        forces = [0.0] * self.N
        total_impulse_x = 0.0
        total_impulse_y = 0.0

        if d_mouse < (self.r0 + 60.0):
            mouse_angle = math.atan2(my, mx)
            if mouse_angle < 0:
                mouse_angle += 2.0 * math.pi

            cursor_speed = math.hypot(self.mouse_v.x(), self.mouse_v.y())

            for i in range(self.N):
                theta = i * self.d_theta
                # Shortest angular distance on circle
                diff = abs(theta - mouse_angle)
                if diff > math.pi:
                    diff = 2.0 * math.pi - diff

                node_r = self.r0 + self.dr[i]
                node_x = node_r * math.cos(theta)
                node_y = node_r * math.sin(theta)

                # Distance from node to cursor center
                dist_to_cursor = math.hypot(node_x - mx, node_y - my)

                if dist_to_cursor < cursor_radius + 18.0:
                    # Penetration depth
                    delta = (cursor_radius + 18.0) - dist_to_cursor
                    # Hertzian contact force ~ delta^1.5
                    f_hertz = self.k_contact * (delta ** 1.5)

                    # Dynamic momentum transfer from moving cursor
                    norm_dir_x = (node_x - mx) / max(0.1, dist_to_cursor)
                    norm_dir_y = (node_y - my) / max(0.1, dist_to_cursor)
                    v_rel = (self.mouse_v.x() * norm_dir_x + self.mouse_v.y() * norm_dir_y)
                    f_dynamic = max(0.0, v_rel * self.c_contact)

                    total_f = -(f_hertz + f_dynamic)
                    forces[i] += total_f

                    total_impulse_x += -total_f * math.cos(theta)
                    total_impulse_y += -total_f * math.sin(theta)

        # 2. Semi-Implicit Euler Numerical Integration
        new_v = [0.0] * self.N
        new_dr = [0.0] * self.N

        for i in range(self.N):
            left = (i - 1) % self.N
            right = (i + 1) % self.N

            # Physics: Hooke's Law + Young-Laplace Surface Tension + Viscous Damping
            f_hooke = -self.k_hooke * self.dr[i]
            f_tension = self.tension * (self.dr[left] + self.dr[right] - 2.0 * self.dr[i])
            f_drag = -self.gamma * self.v[i]
            f_external = forces[i]

            acc = f_hooke + f_tension + f_drag + f_external

            new_v[i] = self.v[i] + acc * self.dt
            new_dr[i] = self.dr[i] + new_v[i] * self.dt

        # 3. Volume Conservation Incompressibility Constraint
        # A solid body cannot change total volume; indentation causes bulging elsewhere
        vol_error = sum(new_dr) / float(self.N)
        for i in range(self.N):
            new_dr[i] -= vol_error

        self.v = new_v
        self.dr = new_dr

        # 4. Center of Mass Dynamics (Translational Inertia)
        cm_acc_x = (total_impulse_x * 0.08 - self.cm_k * self.cm_x - self.cm_damping * self.cm_vx)
        cm_acc_y = (total_impulse_y * 0.08 - self.cm_k * self.cm_y - self.cm_damping * self.cm_vy)
        self.cm_vx += cm_acc_x * self.dt
        self.cm_vy += cm_acc_y * self.dt
        self.cm_x += self.cm_vx * self.dt
        self.cm_y += self.cm_vy * self.dt

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0 + self.cm_x
        cy = h / 2.0 + self.cm_y

        # Deep Neutral Studio Backdrop
        bg = QRadialGradient(w / 2.0, h / 2.0, max(w, h) * 0.65)
        bg.setColorAt(0.0, QColor(24, 28, 38))
        bg.setColorAt(0.7, QColor(13, 16, 23))
        bg.setColorAt(1.0, QColor(7, 9, 13))
        painter.fillRect(self.rect(), bg)

        # Ground Drop Shadow (Realistic Occlusion based on ball proximity)
        shadow_w = self.r0 * 1.55 + self.cm_y * 0.2
        shadow_h = 24.0 - self.cm_y * 0.05
        shadow_y = h / 2.0 + self.r0 + 32.0
        shadow_grad = QRadialGradient(cx, shadow_y, shadow_w / 2.0)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, 140))
        shadow_grad.setColorAt(0.6, QColor(0, 0, 0, 50))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, shadow_y), shadow_w / 2.0, max(4.0, shadow_h))

        # Build Continuous Physical Boundary Path
        path = QPainterPath()
        pts = []
        for i in range(self.N):
            theta = i * self.d_theta
            r = self.r0 + self.dr[i]
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            pts.append(QPointF(x, y))

        path.moveTo(pts[0])
        for i in range(self.N):
            p_next = pts[(i + 1) % self.N]
            mid = QPointF((pts[i].x() + p_next.x()) / 2.0, (pts[i].y() + p_next.y()) / 2.0)
            path.quadTo(pts[i], mid)
        path.closeSubpath()

        # Studio Diffuse Shading (Normalized Key-light from top-left)
        light_pos = QPointF(cx - self.r0 * 0.45, cy - self.r0 * 0.50)
        sphere_mat = QRadialGradient(light_pos, self.r0 * 1.45)
        sphere_mat.setColorAt(0.0, QColor(64, 186, 255))     # Diffuse highlight
        sphere_mat.setColorAt(0.25, QColor(28, 128, 224))    # Midtone
        sphere_mat.setColorAt(0.70, QColor(10, 48, 110))     # Core shadow
        sphere_mat.setColorAt(0.95, QColor(4, 18, 48))       # Umbra boundary
        sphere_mat.setColorAt(1.0, QColor(2, 10, 28))

        painter.setBrush(QBrush(sphere_mat))
        painter.setPen(QPen(QColor(18, 64, 140, 160), 1.2))
        painter.drawPath(path)

        # Physical Specular Glint (Fresnel reflection)
        glint = QRadialGradient(light_pos.x(), light_pos.y(), self.r0 * 0.38)
        glint.setColorAt(0.0, QColor(255, 255, 255, 220))
        glint.setColorAt(0.35, QColor(210, 240, 255, 120))
        glint.setColorAt(0.80, QColor(100, 200, 255, 0))
        painter.setBrush(QBrush(glint))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(light_pos, self.r0 * 0.28, self.r0 * 0.20)

        # Ambient Bounce Light from floor (Subtle upward reflection)
        bounce_pos = QPointF(cx + self.r0 * 0.25, cy + self.r0 * 0.45)
        bounce_grad = QRadialGradient(bounce_pos, self.r0 * 0.55)
        bounce_grad.setColorAt(0.0, QColor(70, 150, 230, 45))
        bounce_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(bounce_grad))
        painter.drawEllipse(bounce_pos, self.r0 * 0.45, self.r0 * 0.30)

        # HUD Info
        painter.setPen(QColor(110, 120, 138, 160))
        painter.setFont(QFont("SF Pro Text", 10))
        painter.drawText(24, 32, "NEWTONIAN CONTINUUM SOLID SPHERE")
        painter.drawText(24, 48, "Mechanics: Young-Laplace Surface Tension • Hertzian Contact • Viscous Drag")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Physical Solid Sphere Engine")
        self.resize(900, 720)
        self.setCentralWidget(RealPhysicsSphere(self))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
