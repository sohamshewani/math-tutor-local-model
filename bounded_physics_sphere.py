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

class BoundedGravitySphereWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Scaled-down radius
        self.r0 = 95.0
        self.N = 96
        self.d_theta = (2.0 * math.pi) / self.N

        # Maximum physical deformation limit (22% of radius)
        self.max_dent = self.r0 * 0.22

        # Viscoelastic state
        self.dr = [0.0] * self.N
        self.v = [0.0] * self.N

        # Dynamics Constants
        self.dt = 1.0 / 60.0
        self.gravity = 920.0
        self.restitution = 0.62

        # Tuned parameters
        self.jiggle_factor = 0.5
        self.k_elastic = 35.0
        self.eta_viscous = 4.2
        self.gamma_drag = 3.6
        self.tension = 12.0
        self.recalc_jiggle_parameters(50)

        # Center of Mass
        self.pos = Vector3(0.0, -100.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)

        # 3D Rotation
        self.rot_x = 0.25
        self.rot_y = -0.35
        self.omega_x = 0.0
        self.omega_y = 0.0

        # Mouse & Hit State
        self.is_pointer_down = False
        self.holding_ball = False
        self.mouse_pos = QPointF(-2000, -2000)
        self.prev_mouse = QPointF(-2000, -2000)
        self.mouse_v = QPointF(0, 0)

        # 60 FPS Loop
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.physics_step)
        self.timer.start(16)

    def recalc_jiggle_parameters(self, slider_val):
        frac = max(0.0, min(1.0, slider_val / 100.0))
        self.jiggle_factor = frac
        # Safe bounded elasticity: retains shape integrity across all slider values
        self.k_elastic = 52.0 - frac * 32.0      # 52 down to 20
        self.gamma_drag = 5.2 - frac * 3.0      # 5.2 down to 2.2
        self.eta_viscous = 5.5 - frac * 3.0     # 5.5 down to 2.5
        self.tension = 18.0 - frac * 10.0       # 18 down to 8.0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pointer_down = True
            self.prev_mouse = event.position()
            self.mouse_pos = event.position()

            cx = self.width() / 2.0 + self.pos.x
            cy = self.height() / 2.0 + self.pos.y
            dist = math.hypot(event.position().x() - cx, event.position().y() - cy)

            if dist <= self.r0 + 8.0:
                self.holding_ball = True
                click_angle = math.atan2(event.position().y() - cy, event.position().x() - cx)
                if click_angle < 0:
                    click_angle += 2.0 * math.pi

                impulse = min(self.max_dent * 1.5, (16.0 + 22.0 * self.jiggle_factor))
                for i in range(self.N):
                    theta = i * self.d_theta
                    diff = abs(theta - click_angle)
                    if diff > math.pi:
                        diff = 2.0 * math.pi - diff
                    if diff < 0.7:
                        envelope = math.cos((diff / 0.7) * (math.pi / 2.0))
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

        # Compute cursor speed
        if self.prev_mouse.x() > -1000:
            self.mouse_v = (self.mouse_pos - self.prev_mouse) / self.dt
        else:
            self.mouse_v = QPointF(0, 0)
        self.prev_mouse = QPointF(self.mouse_pos)

        # 1. External Hit / Batting Collision
        mx = self.mouse_pos.x() - cx
        my = self.mouse_pos.y() - cy
        dist_to_center = math.hypot(mx, my)
        cursor_speed = math.hypot(self.mouse_v.x(), self.mouse_v.y())

        if self.is_pointer_down and not self.holding_ball:
            if dist_to_center <= self.r0 + 18.0 and cursor_speed > 60.0:
                hit_dir_x = self.mouse_v.x() / cursor_speed
                hit_dir_y = self.mouse_v.y() / cursor_speed

                strike_strength = min(900.0, cursor_speed * 0.75)
                self.vel.x += hit_dir_x * strike_strength * 0.35
                self.vel.y += hit_dir_y * strike_strength * 0.35

                self.omega_y += hit_dir_x * 0.08
                self.omega_x -= hit_dir_y * 0.08

                hit_angle = math.atan2(my, mx)
                if hit_angle < 0:
                    hit_angle += 2.0 * math.pi

                wave_impulse = min(self.max_dent * 1.2, (cursor_speed / 28.0) * (0.6 + self.jiggle_factor * 0.8))
                for i in range(self.N):
                    theta = i * self.d_theta
                    diff = abs(theta - hit_angle)
                    if diff > math.pi:
                        diff = 2.0 * math.pi - diff
                    if diff < 0.75:
                        self.v[i] -= wave_impulse * math.cos((diff / 0.75) * (math.pi / 2.0))

        # 2. Strict 4-Sided Containment Boundary (Never Escapes Screen)
        floor_y = self.height() - 55.0
        ceiling_y = 25.0
        wall_padding = 20.0

        min_cx = wall_padding + self.r0
        max_cx = self.width() - wall_padding - self.r0
        min_cy = ceiling_y + self.r0
        max_cy = floor_y - self.r0

        if self.holding_ball and self.is_pointer_down:
            target_cx = max(min_cx, min(max_cx, self.mouse_pos.x()))
            target_cy = max(min_cy, min(max_cy, self.mouse_pos.y()))
            self.vel.x = (target_cx - (self.width() / 2.0 + self.pos.x)) * 14.0
            self.vel.y = (target_cy - (self.height() / 2.0 + self.pos.y)) * 14.0
            self.pos.x = target_cx - self.width() / 2.0
            self.pos.y = target_cy - self.height() / 2.0
        else:
            self.vel.y += self.gravity * self.dt
            self.pos.x += self.vel.x * self.dt
            self.pos.y += self.vel.y * self.dt

            # Left & Right Wall Boundaries
            curr_cx = self.width() / 2.0 + self.pos.x
            if curr_cx < min_cx:
                self.pos.x = min_cx - self.width() / 2.0
                self.vel.x = -self.vel.x * self.restitution
            elif curr_cx > max_cx:
                self.pos.x = max_cx - self.width() / 2.0
                self.vel.x = -self.vel.x * self.restitution

            # Ceiling Boundary
            curr_cy = self.height() / 2.0 + self.pos.y
            if curr_cy < min_cy:
                self.pos.y = min_cy - self.height() / 2.0
                self.vel.y = -self.vel.y * self.restitution

            # Floor Boundary
            if curr_cy > max_cy:
                self.pos.y = max_cy - self.height() / 2.0
                if abs(self.vel.y) > 15.0:
                    impact_v = abs(self.vel.y)
                    self.vel.y = -self.vel.y * self.restitution
                    self.vel.x *= 0.93

                    ground_impulse = min(self.max_dent * 1.4, (impact_v / 22.0) * (0.6 + self.jiggle_factor * 0.8))
                    for i in range(self.N):
                        theta = i * self.d_theta
                        diff = abs(theta - math.pi / 2.0)
                        if diff > math.pi:
                            diff = 2.0 * math.pi - diff
                        if diff < 0.85:
                            self.v[i] -= ground_impulse * math.cos((diff / 0.85) * (math.pi / 2.0))
                else:
                    self.vel.y = 0.0
                    self.vel.x *= 0.88

        self.vel.x *= (1.0 - 0.35 * self.dt)

        # 3. 3D Angular Spin
        self.rot_x += self.omega_x
        self.rot_y += self.omega_y
        self.omega_x *= 0.98
        self.omega_y *= 0.98

        # 4. Viscoelastic Jiggle with Hard Clamping Limits
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
            v_cand = self.v[i] + acc * self.dt
            dr_cand = self.dr[i] + v_cand * self.dt

            # Hard physical constraint: deformation cannot exceed max_dent limit
            if abs(dr_cand) > self.max_dent:
                dr_cand = math.copysign(self.max_dent, dr_cand)
                v_cand = -v_cand * 0.3  # Plastic boundary rebound

            new_v[i] = v_cand
            new_dr[i] = dr_cand

        # Incompressible constant-volume balance
        vol_offset = sum(new_dr) / float(self.N)
        for i in range(self.N):
            new_dr[i] = max(-self.max_dent, min(self.max_dent, new_dr[i] - vol_offset))

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
        floor_y = h - 55.0

        # Background
        bg = QRadialGradient(w / 2.0, h / 2.0, max(w, h) * 0.70)
        bg.setColorAt(0.0, QColor(26, 30, 42))
        bg.setColorAt(0.6, QColor(13, 16, 24))
        bg.setColorAt(1.0, QColor(6, 8, 14))
        painter.fillRect(self.rect(), bg)

        # Floor Baseline
        painter.setPen(QPen(QColor(48, 54, 72, 140), 1.5))
        painter.drawLine(0, int(floor_y), int(w), int(floor_y))

        # Dynamic Floor Shadow
        elevation = max(0.0, floor_y - (cy + self.r0))
        shadow_w = self.r0 * (1.5 + elevation * 0.003)
        shadow_alpha = int(max(10, min(160, 170 - elevation * 0.8)))

        shadow_grad = QRadialGradient(cx, floor_y, shadow_w / 2.0)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, shadow_alpha))
        shadow_grad.setColorAt(0.5, QColor(0, 0, 0, int(shadow_alpha * 0.35)))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, floor_y), shadow_w / 2.0, max(3.0, 16.0 - elevation * 0.05))

        # Hull Construction
        hull_path = QPainterPath()
        pts = []
        for i in range(self.N):
            theta = i * self.d_theta
            r = self.r0 + self.dr[i]
            pts.append(QPointF(cx + r * math.cos(theta), cy + r * math.sin(theta)))

        hull_path.moveTo(pts[0])
        for i in range(self.N):
            next_pt = pts[(i + 1) % self.N]
            mid = QPointF((pts[i].x() + next_pt.x()) / 2.0, (pts[i].y() + next_pt.y()) / 2.0)
            hull_path.quadTo(pts[i], mid)
        hull_path.closeSubpath()

        # Shading
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

        # Latitude Ring Mesh
        painter.save()
        painter.setClipPath(hull_path)
        painter.setPen(QPen(QColor(140, 230, 255, 45), 1.0))

        for lat in [-0.8, -0.4, 0.0, 0.4, 0.8]:
            r_lat = self.r0 * math.cos(lat)
            z_offset = self.r0 * math.sin(lat)
            tilt_y = cy + z_offset * math.cos(self.rot_x) - r_lat * math.sin(self.rot_x) * math.sin(self.rot_y)
            painter.drawEllipse(QPointF(cx, tilt_y), r_lat * abs(math.cos(self.rot_y) + 0.3), r_lat * 0.28)

        # Specular Glint
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
        self.setWindowTitle("Physically Bounded Viscoelastic Sphere")
        self.resize(860, 680)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar
        top_bar = QWidget(self)
        top_bar.setStyleSheet("background-color: #121622; border-bottom: 1px solid #283044; padding: 6px 20px;")
        bar_layout = QHBoxLayout(top_bar)

        title_lbl = QLabel("JIGGLE ELASTICITY:", self)
        title_lbl.setFont(QFont("SF Pro Text", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00e5ff; letter-spacing: 1px;")

        low_lbl = QLabel("Low (Rigid Rubber)", self)
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

        high_lbl = QLabel("High (Controlled Jelly)", self)
        high_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")

        bar_layout.addWidget(title_lbl)
        bar_layout.addSpacing(15)
        bar_layout.addWidget(low_lbl)
        bar_layout.addWidget(self.slider, 1)
        bar_layout.addWidget(high_lbl)

        main_layout.addWidget(top_bar)

        self.canvas = BoundedGravitySphereWidget(self)
        main_layout.addWidget(self.canvas, 1)
        self.slider.valueChanged.connect(self.canvas.recalc_jiggle_parameters)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
