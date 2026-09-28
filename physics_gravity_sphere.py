import sys
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QRadialGradient, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSlider, QLabel
)

class Vector3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, o): return Vector3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vector3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return Vector3(self.x * s, self.y * s, self.z * s)
    def length(self): return math.hypot(math.hypot(self.x, self.y), self.z)

class RealGravitySphereWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Baseline Geometry
        self.r0 = 145.0
        self.N = 96
        self.d_theta = (2.0 * math.pi) / self.N

        # Viscoelastic Shell Perturbation Vectors
        self.dr = [0.0] * self.N
        self.v = [0.0] * self.N

        # Base Physical Tuning
        self.dt = 1.0 / 60.0
        self.gravity = 980.0         # Gravitational acceleration (px/s^2)
        self.restitution = 0.65      # Floor restitution coefficient

        # Jiggle Parameter Scaling (Controlled by Slider: 0 = extreme low, 100 = extreme high)
        self.jiggle_factor = 0.5     # Default mid-level
        self.k_elastic = 26.0
        self.eta_viscous = 3.8
        self.gamma_drag = 2.8
        self.tension = 10.0
        self.recalc_jiggle_parameters(50)

        # Rigid Body 3D Center of Mass
        self.pos = Vector3(0.0, -80.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)

        # 3D Orientation & Angular Momentum
        self.rot_x = 0.2
        self.rot_y = -0.3
        self.omega_x = 0.0
        self.omega_y = 0.0

        # Cursor Interactivity
        self.is_pointer_down = False
        self.holding_ball = False
        self.mouse_pos = QPointF(-2000, -2000)
        self.prev_mouse = QPointF(-2000, -2000)
        self.mouse_v = QPointF(0, 0)

        # Physics Timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.physics_step)
        self.timer.start(16)

    def recalc_jiggle_parameters(self, slider_val):
        # 0 = Extreme low (ultra rigid), 100 = Extreme high (super floppy jelly)
        frac = slider_val / 100.0
        self.jiggle_factor = frac
        # Lower stiffness + lower damping = extreme high jiggle / bounce oscillations
        self.k_elastic = 48.0 - frac * 38.0      # 48 down to 10
        self.gamma_drag = 4.8 - frac * 3.8      # 4.8 down to 1.0
        self.eta_viscous = 5.0 - frac * 3.5     # 5.0 down to 1.5
        self.tension = 16.0 - frac * 11.0       # 16.0 down to 5.0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pointer_down = True
            self.prev_mouse = event.position()
            self.mouse_pos = event.position()

            cx = self.width() / 2.0 + self.pos.x
            cy = self.height() / 2.0 + self.pos.y
            dist = math.hypot(event.position().x() - cx, event.position().y() - cy)

            if dist <= self.r0 + 10.0:
                # Direct click inside ball: grab and deliver localized click shockwave
                self.holding_ball = True
                click_angle = math.atan2(event.position().y() - cy, event.position().x() - cx)
                if click_angle < 0:
                    click_angle += 2.0 * math.pi

                impulse = (28.0 + 32.0 * self.jiggle_factor)
                for i in range(self.N):
                    theta = i * self.d_theta
                    diff = abs(theta - click_angle)
                    if diff > math.pi:
                        diff = 2.0 * math.pi - diff
                    if diff < 0.75:
                        envelope = math.cos((diff / 0.75) * (math.pi / 2.0))
                        self.v[i] -= impulse * envelope
            else:
                self.holding_ball = False

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pointer_down = False
            self.holding_ball = False

    def physics_step(self):
        cx = self.width() / 2.0 + self.pos.x
        cy = self.height() / 2.0 + self.pos.y

        # Compute cursor velocity vector (px/s)
        if self.prev_mouse.x() > -1000:
            self.mouse_v = (self.mouse_pos - self.prev_mouse) / self.dt
        else:
            self.mouse_v = QPointF(0, 0)
        self.prev_mouse = QPointF(self.mouse_pos)

        # 1. External Swipe / Batting Hit Detection
        mx = self.mouse_pos.x() - cx
        my = self.mouse_pos.y() - cy
        dist_to_center = math.hypot(mx, my)
        cursor_speed = math.hypot(self.mouse_v.x(), self.mouse_v.y())

        # If user drags cursor into the perimeter while holding mouse down
        if self.is_pointer_down and not self.holding_ball:
            if dist_to_center <= self.r0 + 25.0 and cursor_speed > 80.0:
                # Strike impact: transfer cursor momentum to sphere center of mass
                hit_dir_x = self.mouse_v.x() / cursor_speed
                hit_dir_y = self.mouse_v.y() / cursor_speed

                strike_strength = min(1100.0, cursor_speed * 0.85)
                self.vel.x += hit_dir_x * strike_strength * 0.45
                self.vel.y += hit_dir_y * strike_strength * 0.45

                # Torque from strike
                self.omega_y += (hit_dir_x) * 0.12
                self.omega_x -= (hit_dir_y) * 0.12

                # Surface indentation dent at point of collision
                hit_angle = math.atan2(my, mx)
                if hit_angle < 0:
                    hit_angle += 2.0 * math.pi

                wave_impulse = min(65.0, (cursor_speed / 20.0) * (0.6 + self.jiggle_factor * 0.8))
                for i in range(self.N):
                    theta = i * self.d_theta
                    diff = abs(theta - hit_angle)
                    if diff > math.pi:
                        diff = 2.0 * math.pi - diff
                    if diff < 0.8:
                        self.v[i] -= wave_impulse * math.cos((diff / 0.8) * (math.pi / 2.0))

        # 2. Gravity & Center of Mass Dynamics
        floor_y = self.height() - 70.0  # Floor plane coordinate

        if self.holding_ball and self.is_pointer_down:
            # User is dragging the ball directly
            target_x = self.mouse_pos.x() - self.width() / 2.0
            target_y = self.mouse_pos.y() - self.height() / 2.0

            # Spring tether to cursor
            self.vel.x = (target_x - self.pos.x) * 16.0
            self.vel.y = (target_y - self.pos.y) * 16.0
            self.pos.x += self.vel.x * self.dt
            self.pos.y += self.vel.y * self.dt

            # Spin from drag
            self.omega_y += (self.vel.x / self.r0) * 0.005
            self.omega_x -= (self.vel.y / self.r0) * 0.005
        else:
            # Apply gravitational acceleration
            self.vel.y += self.gravity * self.dt
            self.pos.x += self.vel.x * self.dt
            self.pos.y += self.vel.y * self.dt

            # Wall boundaries (Left & Right)
            wall_margin = self.width() / 2.0 - self.r0 - 20.0
            if self.pos.x < -wall_margin:
                self.pos.x = -wall_margin
                self.vel.x = -self.vel.x * self.restitution
            elif self.pos.x > wall_margin:
                self.pos.x = wall_margin
                self.vel.x = -self.vel.x * self.restitution

            # Floor Collision Mechanics
            current_bottom = (self.height() / 2.0 + self.pos.y) + self.r0
            if current_bottom >= floor_y:
                penetration = current_bottom - floor_y
                self.pos.y -= penetration

                # Elastic ground rebound
                if abs(self.vel.y) > 20.0:
                    impact_v = abs(self.vel.y)
                    self.vel.y = -self.vel.y * self.restitution
                    self.vel.x *= 0.94  # Ground friction

                    # Ground impact squashes the bottom nodes (theta near pi/2)
                    ground_impulse = min(50.0, (impact_v / 18.0) * (0.5 + self.jiggle_factor * 0.8))
                    for i in range(self.N):
                        theta = i * self.d_theta
                        diff = abs(theta - math.pi / 2.0)
                        if diff > math.pi:
                            diff = 2.0 * math.pi - diff
                        if diff < 0.9:
                            self.v[i] -= ground_impulse * math.cos((diff / 0.9) * (math.pi / 2.0))
                else:
                    self.vel.y = 0.0
                    self.vel.x *= 0.90  # Resting friction

        # Air drag on center of mass
        self.vel.x *= (1.0 - 0.4 * self.dt)

        # 3. 3D Angular Spin Integration
        self.rot_x += self.omega_x
        self.rot_y += self.omega_y
        self.omega_x *= 0.975
        self.omega_y *= 0.975

        # 4. Viscoelastic Continuum Wave Equation (Jiggle Deformation)
        new_v = [0.0] * self.N
        new_dr = [0.0] * self.N

        for i in range(self.N):
            left = (i - 1) % self.N
            right = (i + 1) % self.N

            f_elastic = -self.k_elastic * self.dr[i]
            f_tension = self.tension * (self.dr[left] + self.dr[right] - 2.0 * self.dr[i])
            laplace_v = (self.v[left] + self.v[right] - 2.0 * self.v[i])
            f_viscous = self.eta_viscous * laplace_v
            f_drag = -self.gamma_drag * self.v[i]

            acc = f_elastic + f_tension + f_viscous + f_drag
            new_v[i] = self.v[i] + acc * self.dt
            new_dr[i] = self.dr[i] + new_v[i] * self.dt

        # Incompressible volume preservation (sum of radial variations = 0)
        vol_offset = sum(new_dr) / float(self.N)
        for i in range(self.N):
            new_dr[i] -= vol_offset

        self.v = new_v
        self.dr = new_dr

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())
        cx = w / 2.0 + self.pos.x
        cy = h / 2.0 + self.pos.y
        floor_y = h - 70.0

        # Studio Stage Backdrop
        bg = QRadialGradient(w / 2.0, h / 2.0, max(w, h) * 0.70)
        bg.setColorAt(0.0, QColor(26, 30, 42))
        bg.setColorAt(0.6, QColor(13, 16, 24))
        bg.setColorAt(1.0, QColor(6, 8, 14))
        painter.fillRect(self.rect(), bg)

        # Floor Stage Grid Line
        painter.setPen(QPen(QColor(48, 54, 72, 160), 1.5))
        painter.drawLine(0, int(floor_y), int(w), int(floor_y))

        # Dynamic Floor Shadow (Grows sharper & darker as ball contacts floor)
        elevation = max(0.0, floor_y - (cy + self.r0))
        shadow_w = self.r0 * (1.6 + elevation * 0.003)
        shadow_alpha = int(max(15, min(170, 180 - elevation * 0.7)))

        shadow_grad = QRadialGradient(cx, floor_y, shadow_w / 2.0)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, shadow_alpha))
        shadow_grad.setColorAt(0.5, QColor(0, 0, 0, int(shadow_alpha * 0.35)))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, floor_y), shadow_w / 2.0, max(4.0, 24.0 - elevation * 0.05))

        # Construct 3D Hull Path
        hull_path = QPainterPath()
        pts = []
        for i in range(self.N):
            theta = i * self.d_theta
            r = self.r0 + self.dr[i]
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            pts.append(QPointF(x, y))

        hull_path.moveTo(pts[0])
        for i in range(self.N):
            next_pt = pts[(i + 1) % self.N]
            mid = QPointF((pts[i].x() + next_pt.x()) / 2.0, (pts[i].y() + next_pt.y()) / 2.0)
            hull_path.quadTo(pts[i], mid)
        hull_path.closeSubpath()

        # Volumetric 3D Material Gradient (Azure-Sapphire)
        light_pos = QPointF(cx - self.r0 * 0.40, cy - self.r0 * 0.45)
        sphere_mat = QRadialGradient(light_pos, self.r0 * 1.55)
        sphere_mat.setColorAt(0.0, QColor(95, 215, 255))
        sphere_mat.setColorAt(0.24, QColor(32, 142, 240))
        sphere_mat.setColorAt(0.70, QColor(10, 54, 126))
        sphere_mat.setColorAt(0.94, QColor(4, 22, 58))
        sphere_mat.setColorAt(1.0, QColor(2, 10, 32))

        painter.setBrush(QBrush(sphere_mat))
        painter.setPen(QPen(QColor(18, 62, 130, 180), 1.5))
        painter.drawPath(hull_path)

        # 3D Geodesic Latitude Rings (Rotates with angular velocity)
        painter.save()
        painter.setClipPath(hull_path)
        painter.setPen(QPen(QColor(140, 230, 255, 45), 1.2))

        for lat in [-0.8, -0.4, 0.0, 0.4, 0.8]:
            r_lat = self.r0 * math.cos(lat)
            z_offset = self.r0 * math.sin(lat)
            tilt_y = cy + z_offset * math.cos(self.rot_x) - r_lat * math.sin(self.rot_x) * math.sin(self.rot_y)
            painter.drawEllipse(QPointF(cx, tilt_y), r_lat * abs(math.cos(self.rot_y) + 0.3), r_lat * 0.28)

        # Specular Highlight (Blinn-Phong Glint)
        glint = QRadialGradient(light_pos.x(), light_pos.y(), self.r0 * 0.36)
        glint.setColorAt(0.0, QColor(255, 255, 255, 245))
        glint.setColorAt(0.35, QColor(215, 248, 255, 140))
        glint.setColorAt(0.80, QColor(100, 210, 255, 0))
        painter.setBrush(QBrush(glint))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(light_pos, self.r0 * 0.26, self.r0 * 0.18)
        painter.restore()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Gravitational Viscoelastic Sphere")
        self.resize(960, 760)

        # Root Layout with Top Control Bar
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Jiggle Control Toolbar
        top_bar = QWidget(self)
        top_bar.setStyleSheet("background-color: #121622; border-bottom: 1px solid #283044; padding: 6px 20px;")
        bar_layout = QHBoxLayout(top_bar)

        title_lbl = QLabel("JIGGLE ELASTICITY:", self)
        title_lbl.setFont(QFont("SF Pro Text", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00e5ff; letter-spacing: 1px;")

        low_lbl = QLabel("Extreme Low (Rigid)", self)
        low_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #21262d;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00e5ff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #f0f6fc;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """)

        high_lbl = QLabel("Extreme High (Jelly)", self)
        high_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")

        bar_layout.addWidget(title_lbl)
        bar_layout.addSpacing(15)
        bar_layout.addWidget(low_lbl)
        bar_layout.addWidget(self.slider, 1)
        bar_layout.addWidget(high_lbl)

        main_layout.addWidget(top_bar)

        # Sphere Canvas
        self.canvas = RealGravitySphereWidget(self)
        main_layout.addWidget(self.canvas, 1)

        # Connect Slider to Physics Hook
        self.slider.valueChanged.connect(self.canvas.recalc_jiggle_parameters)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
