"""Synthetic frames for steer_cli: a yellow map, a red arrowhead at a known point, a pale wedge at a
known bearing. Checks the host build calls Find correctly (pixel order, flip, per mille); it says
nothing about Find's own accuracy on real video, which the harness notes measured on 9 Nov."""
import math, sys
import numpy as np
W, H = 1920, 1080
CASES = [(850, 870, 45), (800, 800, 200), (930, 950, 310), (870, 820, 0)]  # x, y per mille; bearing
def frame(px, py, bearing, flip=False):
    img = np.zeros((H, W, 4), np.uint8); img[..., :3] = (60, 90, 50)            # BGR grass
    x0, y0, w, h = 742 * W // 1000, 743 * H // 1000, 250 * W // 1000, 250 * H // 1000
    img[y0 + h // 4: y0 + 3 * h // 4, x0 + w // 5: x0 + 4 * w // 5, :3] = (40, 180, 220)  # yellow map
    cx, cy = px * W / 1000, py * H / 1000
    sx, sy = w / 320, h / 180                                                    # pixels per grid sample
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = (xx - cx) / sx, (yy - cy) / sy
    dist = np.hypot(dx, dy)
    ang = (np.degrees(np.arctan2(dx, -dy)) + 360) % 360
    diff = np.abs((ang - bearing + 180) % 360 - 180)
    img[(dist >= 10) & (dist <= 29) & (diff <= 30), :3] = (200, 205, 205)       # pale wedge
    img[dist <= 4, :3] = (30, 30, 200)                                           # red arrowhead
    return img
if __name__ == "__main__":
    for px, py, b in CASES:
        sys.stdout.buffer.write(frame(px, py, b).tobytes())
