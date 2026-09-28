import sys
import math
import time
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

class TelemetrySphereWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        self.r0 = 90.0
        self.N = 96
        self.d_theta = (2.0 * math.pi) / self.N
        self.max_dent = self.r0 * 0.24

        self.dr = [0.0] * self.N
        self.v = [0.0] * self.N

        self.dt = 1.0 / 60.0
        self.gravity = 980.0

        self.jiggle_factor = 0.5
        self.base_restitution = 0.76
        self.effective_restitution = 0.65
        self.recalc_physics_parameters(50)

        self.pos = Vector3(0.0, -120.0, 0.0)
        self.vel = Vector3(0.0, 0.0, 0.0)

        self.rot_x = 0.25
        self.rot_y = -0.35
        self.omega_x = 0.0
        self.omega_y = 0.0

        self.is_pointer_down = False
        self.holding_ball = False
        self.mouse_pos = QPointF(-2000, -2000)
        self.prev_mouse = QPointF(-2000, -2000)
        self.mouse_v = QPointF(0, 0)

        # Telemetry & Diagnostics Counters
        self.total_calculations = 0
        self.ops_per_second = 0
        self.frame_ops = 0
        self.fps = 60
        self.compute_time_us = 0.0
        self.last_telemetry_time = time.perf_counter()
        self.frame_count = 0
        self.step_ops_accumulator = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.physics_step)
        self.timer.start(16)

    def recalc_physics_parameters(self, slider_val):
        frac = max(0.0, min(1.0, slider_val / 100.0))
        self.jiggle_factor = frac
        self.k_elastic = 56.0 - frac * 38.0
        self.gamma_drag = 5.2 - frac * 3.4
        self.eta_viscous = 5.8 - frac * 3.6
        self.tension = 19.0 - frac * 12.0
        self.effective_restitution = self.base_restitution * (1.0 - frac * 0.35)

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

                impulse = min(self.max_dent * 1.6, (18.0 + 26.0 * self.jiggle_factor))
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

    def trigger_boundary_jiggle(self, normal_angle, impact_speed):
        jiggle_amp = min(self.max_dent * 1.4, (impact_speed / 20.0) * (0.5 + self.jiggle_factor * 1.1))
        for i in range(self.N):
            theta = i * self.d_theta
            diff = abs(theta - normal_angle)
            if diff > math.pi:
                diff = 2.0 * math.pi - diff
            if diff < 0.85:
                self.v[i] -= jiggle_amp * math.cos((diff / 0.85) * (math.pi / 2.0))

    def physics_step(self):
        t0 = time.perf_counter_ns()
        current_ops = 0

        cx = self.width() / 2.0 + self.pos.x
        cy = self.height() / 2.0 + self.pos.y

        if self.prev_mouse.x() > -1000:
            self.mouse_v = (self.mouse_pos - self.prev_mouse) / self.dt
            current_ops += 4
        else:
            self.mouse_v = QPointF(0, 0)
        self.prev_mouse = QPointF(self.mouse_pos)

        # 1. External Strike Collision Check
        mx = self.mouse_pos.x() - cx
        my = self.mouse_pos.y() - cy
        dist_to_center = math.hypot(mx, my)
        cursor_speed = math.hypot(self.mouse_v.x(), self.mouse_v.y())
        current_ops += 12

        if self.is_pointer_down and not self.holding_ball:
            if dist_to_center <= self.r0 + 20.0 and cursor_speed > 60.0:
                hit_dir_x = self.mouse_v.x() / cursor_speed
                hit_dir_y = self.mouse_v.y() / cursor_speed
                strike_impulse = min(950.0, cursor_speed * 0.80)
                self.vel.x += hit_dir_x * strike_impulse * 0.38
                self.vel.y += hit_dir_y * strike_impulse * 0.38
                self.omega_y += hit_dir_x * 0.09
                self.omega_x -= hit_dir_y * 0.09
                hit_angle = math.atan2(my, mx)
                if hit_angle < 0:
                    hit_angle += 2.0 * math.pi
                self.trigger_boundary_jiggle(hit_angle, cursor_speed)
                current_ops += 96 * 8 + 25

        # 2. Strict Boundary Constraints
        floor_y = self.height() - 55.0
        ceiling_y = 25.0
        wall_pad = 20.0
        min_cx = wall_pad + self.r0
        max_cx = self.width() - wall_pad - self.r0
        min_cy = ceiling_y + self.r0
        max_cy = floor_y - self.r0
        current_ops += 8

        if self.holding_ball and self.is_pointer_down:
            target_cx = max(min_cx, min(max_cx, self.mouse_pos.x()))
            target_cy = max(min_cy, min(max_cy, self.mouse_pos.y()))
            self.vel.x = (target_cx - (self.width() / 2.0 + self.pos.x)) * 14.0
            self.vel.y = (target_cy - (self.height() / 2.0 + self.pos.y)) * 14.0
            self.pos.x = target_cx - self.width() / 2.0
            self.pos.y = target_cy - self.height() / 2.0
            current_ops += 18
        else:
            self.vel.y += self.gravity * self.dt
            self.pos.x += self.vel.x * self.dt
            self.pos.y += self.vel.y * self.dt
            current_ops += 6

            curr_cx = self.width() / 2.0 + self.pos.x
            curr_cy = self.height() / 2.0 + self.pos.y

            if curr_cx < min_cx:
                self.pos.x = min_cx - self.width() / 2.0
                impact_vx = abs(self.vel.x)
                self.vel.x = impact_vx * self.effective_restitution
                self.trigger_boundary_jiggle(math.pi, impact_vx)
                current_ops += 96 * 8 + 10
            elif curr_cx > max_cx:
                self.pos.x = max_cx - self.width() / 2.0
                impact_vx = abs(self.vel.x)
                self.vel.x = -impact_vx * self.effective_restitution
                self.trigger_boundary_jiggle(0.0, impact_vx)
                current_ops += 96 * 8 + 10

            if curr_cy < min_cy:
                self.pos.y = min_cy - self.height() / 2.0
                impact_vy = abs(self.vel.y)
                self.vel.y = impact_vy * self.effective_restitution
                self.trigger_boundary_jiggle(3.0 * math.pi / 2.0, impact_vy)
                current_ops += 96 * 8 + 10
            elif curr_cy > max_cy:
                self.pos.y = max_cy - self.height() / 2.0
                impact_vy = abs(self.vel.y)
                if impact_vy > 18.0:
                    self.vel.y = -impact_vy * self.effective_restitution
                    self.vel.x *= 0.92
                    self.trigger_boundary_jiggle(math.pi / 2.0, impact_vy)
                    current_ops += 96 * 8 + 15
                else:
                    self.vel.y = 0.0
                    self.vel.x *= 0.88
                    current_ops += 2

        self.vel.x *= (1.0 - 0.30 * self.dt)
        self.rot_x += self.omega_x
        self.rot_y += self.omega_y
        self.omega_x *= 0.982
        self.omega_y *= 0.982
        current_ops += 9

        # 3. Continuum Mesh Integration (96 nodes)
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

            if abs(dr_cand) > self.max_dent:
                dr_cand = math.copysign(self.max_dent, dr_cand)
                v_cand = -v_cand * 0.25

            new_v[i] = v_cand
            new_dr[i] = dr_cand

        current_ops += self.N * 16

        vol_offset = sum(new_dr) / float(self.N)
        for i in range(self.N):
            new_dr[i] = max(-self.max_dent, min(self.max_dent, new_dr[i] - vol_offset))
        current_ops += self.N * 3 + 1

        self.v = new_v
        self.dr = new_dr

        # Rendering ops budget
        current_ops += (self.N * 4) + (self.N * 6) + 45 + 20

        t1 = time.perf_counter_ns()
        self.compute_time_us = (t1 - t0) / 1000.0

        # Accumulate telemetry
        self.frame_ops = current_ops
        self.total_calculations += current_ops
        self.step_ops_accumulator += current_ops
        self.frame_count += 1

        now = time.perf_counter()
        if now - self.last_telemetry_time >= 0.5:
            elapsed = now - self.last_telemetry_time
            self.fps = int(self.frame_count / elapsed)
            self.ops_per_second = int(self.step_ops_accumulator / elapsed)
            self.frame_count = 0
            self.step_ops_accumulator = 0
            self.last_telemetry_time = now

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
        bg.setColorAt(0.0, QColor(24, 28, 40))
        bg.setColorAt(0.6, QColor(12, 15, 22))
        bg.setColorAt(1.0, QColor(6, 8, 12))
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

        # Volumetric 3D Shading
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

        # 3D Rotating Geodesic Rings
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

        # --- LIVE TELEMETRY HUD OVERLAY (TOP-LEFT) ---
        hud_box = QWidget(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(10, 14, 22, 210))
        painter.drawRoundedRect(18, 16, 290, 116, 8, 8)

        painter.setPen(QPen(QColor(0, 229, 255, 160), 1.0))
        painter.drawRoundedRect(18, 16, 290, 116, 8, 8)

        painter.setFont(QFont("Menlo", 10, QFont.Weight.Bold))
        painter.setPen(QColor(0, 229, 255))
        painter.drawText(30, 36, "PHYSICS ENGINE TELEMETRY")

        painter.setFont(QFont("Menlo", 9))
        painter.setPen(QColor(220, 230, 242))
        painter.drawText(30, 56, f"Frame Rate:       {self.fps} FPS")
        painter.drawText(30, 72, f"Ops This Step:    {self.frame_ops:,} FLOPs")
        painter.drawText(30, 88, f"Throughput:       {self.ops_per_second:,} FLOPs/s")
        painter.drawText(30, 104, f"Solve Latency:    {self.compute_time_us:.1f} µs")
        painter.drawText(30, 120, f"Total Computed:   {self.total_calculations:,}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coupled Physics Sphere with Real-Time Telemetry HUD")
        self.resize(880, 700)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = QWidget(self)
        top_bar.setStyleSheet("background-color: #121622; border-bottom: 1px solid #283044; padding: 6px 20px;")
        bar_layout = QHBoxLayout(top_bar)

        title_lbl = QLabel("JIGGLE ELASTICITY:", self)
        title_lbl.setFont(QFont("SF Pro Text", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00e5ff; letter-spacing: 1px;")

        low_lbl = QLabel("Rigid", self)
        low_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: #21262d; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #00e5ff; border-radius: 3px; }
            QSlider::handle:horizontal { background: #f0f6fc; width: 16px; margin: -5px 0; border-radius: 8px; }
        """)

        high_lbl = QLabel("Jelly", self)
        high_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")

        bar_layout.addWidget(title_lbl)
        bar_layout.addSpacing(15)
        bar_layout.addWidget(low_lbl)
        bar_layout.addWidget(self.slider, 1)
        bar_layout.addWidget(high_lbl)

        main_layout.addWidget(top_bar)

        self.canvas = TelemetrySphereWidget(self)
        main_layout.addWidget(self.canvas, 1)
        self.slider.valueChanged.connect(self.canvas.recalc_physics_parameters)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
