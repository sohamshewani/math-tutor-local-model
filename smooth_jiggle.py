import sys
import tty
import termios
import select
import math
import time
import os

def enable_mouse():
    # SGR mouse tracking mode (movement without click + clicks)
    sys.stdout.write("\033[?1000h\033[?1002h\033[?1003h\033[?1006h")
    # Hide terminal cursor and alternate screen buffer
    sys.stdout.write("\033[?25l\033[?1049h")
    sys.stdout.flush()

def disable_mouse():
    # Restore normal mouse, show cursor, leave alternate buffer
    sys.stdout.write("\033[?1000l\033[?1002l\033[?1003l\033[?1006l")
    sys.stdout.write("\033[?25h\033[?1049l")
    sys.stdout.flush()

def main():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)
    enable_mouse()

    # Physics state for 3D elastic deformation
    dent_x = 0.0
    dent_y = 0.0
    dent_depth = 0.0
    dent_vel = 0.0
    spring_k = 0.18
    damping = 0.85

    mouse_x = -999.0
    mouse_y = -999.0

    # Spherical radius in 3D unit space
    base_radius = 1.05

    # Light direction (normalized)
    lx, ly, lz = -0.577, -0.577, 0.577

    try:
        while True:
            # Check terminal size
            cols, rows = os.get_terminal_size()
            width = cols
            # Each character cell renders 2 vertical subpixels via upper/lower half blocks
            height_subpixels = (rows - 1) * 2

            # Non-blocking input reading
            r, _, _ = select.select([sys.stdin], [], [], 0.016)
            if r:
                buf = sys.stdin.read(256)
                if '\x03' in buf or 'q' in buf or 'Q' in buf:
                    break
                
                # Parse mouse coordinates: \033[<0;X;YM or m
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
                                # Translate character cell to sub-pixel coordinates
                                mouse_x = float(parts[1]) - 1
                                mouse_y = (float(parts[2]) - 1) * 2.0
                            except ValueError:
                                pass
                        idx = e_idx + 1
                    else:
                        break

            # Map mouse to normalized -1.0 to 1.0 coordinate space
            aspect = (width / height_subpixels) * 0.95
            scale = min(width / 2.4, height_subpixels / 2.4)
            center_x = width / 2.0
            center_y = height_subpixels / 2.0

            norm_mx = (mouse_x - center_x) / scale
            norm_my = (mouse_y - center_y) / scale
            m_dist = math.sqrt(norm_mx * norm_mx + norm_my * norm_my)

            # Interactive deformation logic
            if m_dist < base_radius + 0.35:
                # Target squish depth proportional to how deep cursor enters
                target_depth = max(0.0, (base_radius + 0.35) - m_dist) * 0.75
                dent_x = norm_mx
                dent_y = norm_my
                dent_vel += (target_depth - dent_depth) * 0.3
            else:
                target_depth = 0.0

            # Spring physics update for the jiggle oscillation
            force = -spring_k * (dent_depth - target_depth)
            dent_vel = (dent_vel + force) * damping
            dent_depth += dent_vel

            # Render Sub-pixel RGB Buffer
            # Buffer size: width * height_subpixels
            # Each entry is (r, g, b)
            pixels = [(13, 17, 23)] * (width * height_subpixels)

            # Ray marching the solid sphere SDF
            for py in range(height_subpixels):
                ny = (py - center_y) / scale
                row_offset = py * width
                for px in range(width):
                    nx = (px - center_x) / scale

                    # Radial distance from ball origin
                    r2 = nx * nx + ny * ny
                    
                    # Local jiggle distortion based on cursor dent position
                    dx = nx - dent_x
                    dy = ny - dent_y
                    dist_to_dent = math.sqrt(dx * dx + dy * dy)
                    
                    # Soft Gaussian deformation envelope
                    deform = dent_depth * math.exp(-(dist_to_dent * dist_to_dent) / 0.18)
                    effective_radius = base_radius - deform

                    if r2 <= effective_radius * effective_radius:
                        # Exact sphere height on Z-axis
                        nz = math.sqrt(max(0.0, effective_radius * effective_radius - r2))
                        
                        # Normal vector at surface
                        norm_len = math.sqrt(r2 + nz * nz)
                        norm_x = nx / norm_len
                        norm_y = ny / norm_len
                        norm_z = nz / norm_len

                        # Diffuse Lambertian Shading
                        diff = max(0.0, norm_x * lx + norm_y * ly + norm_z * lz)

                        # Specular Blinn-Phong Glint (glossy highlight)
                        # Light vector + View vector ([0, 0, 1]) -> Half vector
                        hx, hy, hz = lx, ly, lz + 1.0
                        h_len = math.sqrt(hx*hx + hy*hy + hz*hz)
                        spec = max(0.0, (norm_x * hx + norm_y * hy + norm_z * hz) / h_len) ** 24

                        # Ambient + Diffuse (Cyan/Deep Teal palette) + Specular
                        base_r = int(10 + diff * 0 + spec * 220)
                        base_g = int(45 + diff * 175 + spec * 240)
                        base_b = int(70 + diff * 185 + spec * 255)

                        pixels[row_offset + px] = (
                            min(255, base_r),
                            min(255, base_g),
                            min(255, base_b)
                        )
                    elif r2 <= (effective_radius + 0.08) ** 2:
                        # Smooth anti-aliased border rim
                        pixels[row_offset + px] = (0, 100, 140)

            # Render half-block subpixels into terminal string
            # '▀' has top half as foreground and bottom half as background
            lines = []
            for y_cell in range(rows - 1):
                top_y = y_cell * 2
                bot_y = top_y + 1
                line_parts = []
                for px in range(width):
                    tr, tg, tb = pixels[top_y * width + px]
                    br, bg, bb = pixels[bot_y * width + px]
                    line_parts.append(f"\033[38;2;{tr};{tg};{tb};48;2;{br};{bg};{bb}m▀")
                lines.append("".join(line_parts))

            # Atomic ANSI frame push to eliminate flicker
            sys.stdout.write("\033[H" + "\033[0m\n".join(lines) + "\033[0m")
            sys.stdout.flush()

            time.sleep(0.016)

    finally:
        disable_mouse()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    main()
