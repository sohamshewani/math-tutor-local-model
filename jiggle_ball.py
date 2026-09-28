import sys
import tty
import termios
import select
import math
import time
import os

class Node:
    def __init__(self, x, y, z):
        self.ox = x
        self.oy = y
        self.oz = z
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

def create_sphere(radius=1.0, lat_steps=18, lon_steps=36):
    nodes = []
    for i in range(lat_steps + 1):
        lat = math.pi * (-0.5 + float(i) / lat_steps)
        cos_lat = math.cos(lat)
        sin_lat = math.sin(lat)
        for j in range(lon_steps):
            lon = 2 * math.pi * float(j) / lon_steps
            x = radius * math.cos(lon) * cos_lat
            y = radius * math.sin(lon) * cos_lat
            z = radius * sin_lat
            nodes.append(Node(x, y, z))
    return nodes

def enable_mouse():
    # Enable standard and SGR 1006 extended mouse movement tracking
    sys.stdout.write("\033[?1000h\033[?1002h\033[?1003h\033[?1006h")
    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def disable_mouse():
    sys.stdout.write("\033[?1000l\033[?1002l\033[?1003l\033[?1006l")
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def main():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)
    enable_mouse()

    nodes = create_sphere(radius=1.1, lat_steps=16, lon_steps=32)

    rot_x = 0.0
    rot_y = 0.0
    mouse_x = 9999
    mouse_y = 9999
    prev_mx = 9999
    prev_my = 9999

    chars = " .:-=+*#%@"
    stiffness = 0.28
    damping = 0.88

    try:
        # Clear screen once
        sys.stdout.write("\033[2J")
        
        while True:
            # Get terminal size
            cols, rows = os.get_terminal_size()
            width, height = cols, rows - 1

            # Read non-blocking input / mouse sequences
            r, _, _ = select.select([sys.stdin], [], [], 0.016)
            if r:
                buf = sys.stdin.read(128)
                if '\x03' in buf or 'q' in buf or 'Q' in buf:  # Ctrl+C or Q
                    break
                
                # Parse SGR mouse coordinates: \033[<0;X;YM or m
                idx = 0
                while idx < len(buf):
                    s_idx = buf.find("\033[<", idx)
                    if s_idx == -1:
                        break
                    e_idx = -1
                    for k in range(s_idx + 3, len(buf)):
                        if buf[k] in ('M', 'm'):
                            e_idx = k
                            break
                    if e_idx != -1:
                        chunk = buf[s_idx + 3 : e_idx]
                        parts = chunk.split(';')
                        if len(parts) >= 3:
                            try:
                                mouse_x = int(parts[1])
                                mouse_y = int(parts[2])
                            except ValueError:
                                pass
                        idx = e_idx + 1
                    else:
                        break

            # Calculate cursor velocity to trigger impact
            m_vx = (mouse_x - prev_mx) if prev_mx != 9999 else 0
            m_vy = (mouse_y - prev_my) if prev_my != 9999 else 0
            prev_mx, prev_my = mouse_x, mouse_y

            # Idle slow spin
            rot_x += 0.02
            rot_y += 0.035

            cx, sx = math.cos(rot_x), math.sin(rot_x)
            cy, sy = math.cos(rot_y), math.sin(rot_y)

            # Center offsets
            mid_x = width // 2
            mid_y = height // 2
            scale_x = min(width, height * 2) * 0.42
            scale_y = scale_x * 0.50  # Aspect ratio compensation for fonts

            # Physics Update: Spring-Mass Jiggle & Interaction
            for n in nodes:
                # 3D rotation transform
                rx = n.x * cy + n.z * sy
                rz = -n.x * sy + n.z * cy
                ry = n.y * cx - rz * sx
                rz = n.y * sx + rz * cx

                # Perspective projection to screen coordinates
                dist = 3.2
                proj = dist / (dist + rz)
                scr_x = int(mid_x + rx * scale_x * proj)
                scr_y = int(mid_y + ry * scale_y * proj)

                # Collision check with mouse
                dx = scr_x - mouse_x
                dy = (scr_y - mouse_y) * 2.0  # Aspect adjust
                d_sq = dx * dx + dy * dy

                # If mouse touches or passes near the node
                if d_sq < 36:
                    force = (6.0 - math.sqrt(max(0.1, d_sq))) * 0.12
                    # Displace along vertex normal + mouse velocity impact
                    n.vx += (n.ox * force) + (m_vx * 0.015)
                    n.vy += (n.oy * force) + (m_vy * 0.015)
                    n.vz += (n.oz * force)

                # Spring force toward original rest position
                fx = -stiffness * (n.x - n.ox)
                fy = -stiffness * (n.y - n.oy)
                fz = -stiffness * (n.z - n.oz)

                n.vx = (n.vx + fx) * damping
                n.vy = (n.vy + fy) * damping
                n.vz = (n.vz + fz) * damping

                n.x += n.vx
                n.y += n.vy
                n.z += n.vz

            # Render Buffer: Depth & Screen Char Arrays
            screen = [' '] * (width * height)
            zbuffer = [-9999.0] * (width * height)

            # Render vertices and surface shading
            for n in nodes:
                # Rotated coords
                rx = n.x * cy + n.z * sy
                rz = -n.x * sy + n.z * cy
                ry = n.y * cx - rz * sx
                rz = n.y * sx + rz * cx

                dist = 3.2
                proj = dist / (dist + rz)
                sx_coord = int(mid_x + rx * scale_x * proj)
                sy_coord = int(mid_y + ry * scale_y * proj)

                if 0 <= sx_coord < width and 0 <= sy_coord < height:
                    # Directional light source from top-left ([-1, -1, -1])
                    l_dot = -(rx * 0.57 + ry * 0.57 - rz * 0.57)
                    idx = int(max(0, min(1, (l_dot + 1.2) / 2.2)) * (len(chars) - 1))
                    ch = chars[idx]

                    buf_idx = sy_coord * width + sx_coord
                    depth = 1.0 / (dist + rz)
                    if depth > zbuffer[buf_idx]:
                        zbuffer[buf_idx] = depth
                        screen[buf_idx] = ch

            # Display frame with cyan glow
            frame = "\033[H\033[36m" + "\n".join(
                "".join(screen[r * width : (r + 1) * width]) for r in range(height)
            ) + "\033[0m"
            sys.stdout.write(frame)
            sys.stdout.flush()

            time.sleep(0.016)

    finally:
        disable_mouse()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
