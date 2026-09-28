import sys
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QRadialGradient, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget

class Vector3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, o): return Vector3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vector3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return Vector3(self.x * s, self.y * s, self.z * s)
    def dot(self, o): return self.x * o.x + self.y * o.y + self.z * o.z
    def length(self): return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    def normalize(self):
        l = self.length()
        return Vector3(self.x / l, self.y / l, self.z / l) if l > 1e-7 else Vector3(0, 0, 1)

class Realistic3DSphere(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Baseline 3D Geometry
        self.r0 = 160.0
        self.N = 96
        self.d_theta = (2.0 * math.pi) / self.N

        # Kelvin-Voigt Viscoelastic Shell State
        self.dr = [0.0] * self.N
        self.v = [0.0] * self.N

        # Physical Constants
        self.dt = 1.0 / 60.0
        self.k_elastic = 28.0     # Young's modulus equivalent
        self.eta_viscous = 4.2    # Internal shear viscosity
        self.gamma_drag = 3.2     # Viscous drag damping
        self.laplace_tension = 12.0 # Membrane surface tension

        # 3D Rigid-Body Dynamics (Center of Mass & Rotation)
        self.pos_3d = Vector3(0.0, 0.0, 0.0)
        self.vel_3d = Vector3(0.0, 0.0, 0.0)
        self.k_origin = 12.0
        self.drag_cm = 3.0

        # Orientation & Angular Velocity
        self.rot_x = 0.3
        self.rot_y = -0.4
        self.omega_x = 0.0
        self.omega_y = 0.0
        self.rot_damping = 0.965

        # Mouse & Drag State
        self.is_dragging = False
        self.drag_start = QPointF(0, 0)
        self.last_mouse = QPointF(0, 0)
        self.mouse_pos = QPointF(-2000, -2000)

        # 60 FPS Engine Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.physics_step)
        self.timer.start(16)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            cx = self.width() / 2.0 + self.pos_3d.x
            cy = self.height() / 2.0 + self.pos_3d.y
            mx = event.position().x() - cx
            my = event.position().y() - cy
            dist = math.hypot(mx, my)

            # Trigger physical contact impulse (Click Jiggle)
            if dist <= self.r0 + 12.0:
                self.is_dragging = True
                self.drag_start = event.position()
                self.last_mouse = event.position()

                # Hertzian Contact Normal Impulse
                click_angle = math.atan2(my, mx)
                if click_angle < 0:
                    click_angle += 2.0 * math.pi

                impulse = 42.0 * (1.0 - (dist / (self.r0 + 12.0)) * 0.4)
                for i in range(self.N):
                    theta = i * self.d_theta
                    diff = abs(theta - click_angle)
                    if diff > math.pi:
                        diff = 2.0 * math.pi - diff
                    if diff < 0.8:
                        envelope = math.cos((diff / 0.8) * (math.pi / 2.0))
                        self.v[i] -= impulse * envelope

                # 3D Depth displacement bounce
                self.vel_3d.z -= impulse * 0.4

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position()
        if self.is_dragging:
            dx = event.position().x() - self.last_mouse.x()
            dy = event.position().y() - self.last_mouse.y()
            self.last_mouse = event.position()

            # Drag force translates 3D position
            self.pos_3d.x += dx * 0.85
            self.pos_3d.y += dy * 0.85
            self.vel_3d.x = dx / self.dt
            self.vel_3d.y = dy / self.dt

            # Surface traction generates 3D torque (Angular Acceleration)
            # Moment of Inertia for solid sphere: I = (2/5) m r^2
            self.omega_y += (dx / self.r0) * 0.15
            self.omega_x -= (dy / self.r0) * 0.15

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def physics_step(self):
        # 1. 3D Rigid-Body Restoring Mechanics (Elastic Tether toward viewport center)
        if not self.is_dragging:
            f_res_x = -self.k_origin * self.pos_3d.x - self.drag_cm * self.vel_3d.x
            f_res_y = -self.k_origin * self.pos_3d.y - self.drag_cm * self.vel_3d.y
            f_res_z = -self.k_origin * self.pos_3d.z - self.drag_cm * self.vel_3d.z

            self.vel_3d.x += f_res_x * self.dt
            self.vel_3d.y += f_res_y * self.dt
            self.vel_3d.z += f_res_z * self.dt

            self.pos_3d.x += self.vel_3d.x * self.dt
            self.pos_3d.y += self.vel_3d.y * self.dt
            self.pos_3d.z += self.vel_3d.z * self.dt

        # 2. 3D Angular Integration & Friction
        self.rot_x += self.omega_x
        self.rot_y += self.omega_y
        self.omega_x *= self.rot_damping
        self.omega_y *= self.rot_damping

        # 3. Viscoelastic Continuum Wave Dynamics (Kelvin-Voigt Equation)
        new_v = [0.0] * self.N
        new_dr = [0.0] * self.N

        for i in range(self.N):
            prev_idx = (i - 1) % self.N
            next_idx = (i + 1) % self.N

            # Elastic restoring (Hookean) + Surface tension (Young-Laplace)
            f_elastic = -self.k_elastic * self.dr[i]
            f_tension = self.laplace_tension * (self.dr[prev_idx] + self.dr[next_idx] - 2.0 * self.dr[i])

            # Internal shear viscosity + Fluid Drag
            d_vel_laplacian = (self.v[prev_idx] + self.v[next_idx] - 2.0 * self.v[i])
            f_viscous = self.eta_viscous * d_vel_laplacian
            f_drag = -self.gamma_drag * self.v[i]

            acc = f_elastic + f_tension + f_viscous + f_drag

            new_v[i] = self.v[i] + acc * self.dt
            new_dr[i] = self.dr[i] + new_v[i] * self.dt

        # 4. Incompressible Continuum Volume Preservation
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

        # Perspective Camera Projection
        focal_length = 850.0
        z_eff = max(-400.0, self.pos_3d.z)
        proj_scale = focal_length / (focal_length + z_eff)

        cx = w / 2.0 + self.pos_3d.x * proj_scale
        cy = h / 2.0 + self.pos_3d.y * proj_scale
        current_r0 = self.r0 * proj_scale

        # 1. Dark Studio Studio Vignette
        bg = QRadialGradient(w / 2.0, h / 2.0, max(w, h) * 0.70)
        bg.setColorAt(0.0, QColor(24, 28, 38))
        bg.setColorAt(0.6, QColor(12, 15, 22))
        bg.setColorAt(1.0, QColor(6, 8, 12))
        painter.fillRect(self.rect(), bg)

        # 2. Dynamic 3D Contact Floor Shadow (scales with Z elevation)
        floor_y = h / 2.0 + self.r0 + 45.0
        shadow_dist = max(5.0, floor_y - cy)
        shadow_blur = current_r0 * (1.1 + shadow_dist * 0.003)
        shadow_alpha = int(max(20, min(160, 200 - shadow_dist * 0.6)))

        shadow_grad = QRadialGradient(cx, floor_y, shadow_blur)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, shadow_alpha))
        shadow_grad.setColorAt(0.5, QColor(0, 0, 0, int(shadow_alpha * 0.4)))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, floor_y), shadow_blur, max(6.0, 28.0 * proj_scale))

        # 3. Construct 3D Deformed Hull
        hull_path = QPainterPath()
        pts = []
        for i in range(self.N):
            theta = i * self.d_theta
            r = current_r0 + self.dr[i] * proj_scale
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            pts.append(QPointF(x, y))

        hull_path.moveTo(pts[0])
        for i in range(self.N):
            next_pt = pts[(i + 1) % self.N]
            mid = QPointF((pts[i].x() + next_pt.x()) / 2.0, (pts[i].y() + next_pt.y()) / 2.0)
            hull_path.quadTo(pts[i], mid)
        hull_path.closeSubpath()

        # 4. Physically-Based Shading (Key-Light & Umbra Falloff)
        light_pos = QPointF(cx - current_r0 * 0.42, cy - current_r0 * 0.46)
        sphere_pbr = QRadialGradient(light_pos, current_r0 * 1.50)
        sphere_pbr.setColorAt(0.0, QColor(80, 205, 255))     # Diffuse highlight
        sphere_pbr.setColorAt(0.22, QColor(26, 138, 235))   # Solid midtone
        sphere_pbr.setColorAt(0.68, QColor(8, 52, 118))     # Terminator shadow
        sphere_pbr.setColorAt(0.92, QColor(4, 20, 52))      # Core occlusion
        sphere_pbr.setColorAt(1.0, QColor(2, 10, 28))

        painter.setBrush(QBrush(sphere_pbr))
        painter.setPen(QPen(QColor(16, 56, 120, 180), 1.5))
        painter.drawPath(hull_path)

        # 5. Rotating 3D Latitude/Longitude Geodesic Rings (Visualizes 3D rotation)
        painter.save()
        painter.setClipPath(hull_path)
        painter.setPen(QPen(QColor(120, 220, 255, 38), 1.2))

        # Rotate axes based on current angular orientation
        for lat in [-0.8, -0.4, 0.0, 0.4, 0.8]:
            r_lat = current_r0 * math.cos(lat)
            z_offset = current_r0 * math.sin(lat)
            tilt_y = cy + z_offset * math.cos(self.rot_x) - r_lat * math.sin(self.rot_x) * math.sin(self.rot_y)
            painter.drawEllipse(QPointF(cx, tilt_y), r_lat * abs(math.cos(self.rot_y) + 0.3), r_lat * 0.28)

        # 6. Physical Blinn-Phong Glint (Microfacet Specular)
        glint = QRadialGradient(light_pos.x(), light_pos.y(), current_r0 * 0.35)
        glint.setColorAt(0.0, QColor(255, 255, 255, 245))
        glint.setColorAt(0.35, QColor(210, 245, 255, 140))
        glint.setColorAt(0.80, QColor(100, 205, 255, 0))
        painter.setBrush(QBrush(glint))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(light_pos, current_r0 * 0.26, current_r0 * 0.18)

        # 7. Ground Fresnel Bounce Reflection
        bounce_pos = QPointF(cx + current_r0 * 0.25, cy + current_r0 * 0.44)
        bounce_grad = QRadialGradient(bounce_pos, current_r0 * 0.60)
        bounce_grad.setColorAt(0.0, QColor(60, 160, 240, 50))
        bounce_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(bounce_grad))
        painter.drawEllipse(bounce_pos, current_r0 * 0.45, current_r0 * 0.28)
        painter.restore()

        # Telemetry Display
        painter.setPen(QColor(120, 130, 150, 180))
        painter.setFont(QFont("SF Pro Text", 10))
        painter.drawText(24, 32, "3D VISCOELASTIC SOLID CONTINUUM // PBR")
        painter.drawText(24, 48, "Click: Impact Shockwave (Jiggle) | Drag: 3D Inertial Rotation & Translation")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Viscoelastic Continuum Sphere")
        self.resize(920, 720)
        self.setCentralWidget(Realistic3DSphere(self))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
