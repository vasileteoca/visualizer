import numpy as np
import random

# ==============================
# Config
# ==============================
VIS_WIDTH, VIS_HEIGHT = 1200, 960
ROWS, COLS = VIS_HEIGHT, VIS_WIDTH
DAMPING = 0.995
NUM_DISTURBANCES = 10
THRESHOLD = 0.0001

# ==============================
# Buffers
# ==============================
current = np.zeros((ROWS, COLS), dtype=np.float32)
previous = np.zeros((ROWS, COLS), dtype=np.float32)

# ==============================
# Water Disturbances
# ==============================
def disturb_water_point(amplitude):
    if amplitude > THRESHOLD:
        for _ in range(NUM_DISTURBANCES):
            y = random.randint(1, ROWS - 2)
            x = random.randint(1, COLS - 2)
            current[y, x] = amplitude


def disturb_water_circle(amplitude):
    if amplitude > THRESHOLD:
        for _ in range(NUM_DISTURBANCES):
            y = random.randint(50, ROWS - 51)
            x = random.randint(50, COLS - 51)
            radius = random.randint(20, 40)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance <= radius:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < ROWS and 0 <= nx < COLS:
                            falloff = (1 - distance / radius) ** 2
                            current[ny, nx] += amplitude * falloff


def disturb_water_blue_shadow(amplitude):
    if amplitude > THRESHOLD:
        for _ in range(NUM_DISTURBANCES):
            y = random.randint(50, ROWS - 51)
            x = random.randint(50, COLS - 51)
            radius = random.randint(40, 80)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    distance = (dx * dx + dy * dy) ** 0.5
                    if distance <= radius:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < ROWS and 0 <= nx < COLS:
                            falloff = (1 - distance / radius) ** 1.5
                            current[ny, nx] += amplitude * falloff * 1.5


# ==============================
# Water simulation update
# ==============================
def update_water_reflecting():
    global current, previous
    new = np.zeros_like(current)

    # Inner grid update
    new[1:-1, 1:-1] = (
        (current[:-2, 1:-1] + current[2:, 1:-1] + current[1:-1, :-2] + current[1:-1, 2:]) / 2
    ) - previous[1:-1, 1:-1]

    # Damping
    new[1:-1, 1:-1] *= DAMPING

    # Reflect edges
    new[0, :] = new[1, :]
    new[-1, :] = new[-2, :]
    new[:, 0] = new[:, 1]
    new[:, -1] = new[:, -2]

    # Reflect corners
    new[0, 0] = new[1, 1]
    new[0, -1] = new[1, -2]
    new[-1, 0] = new[-2, 1]
    new[-1, -1] = new[-2, -2]

    # Update buffers
    previous[:] = current
    current[:] = new


# ==============================
# Visualization helper
# ==============================
def map_to_blue_gradient(field):
    norm = np.clip((field - field.min()) / (field.max() - field.min() + 1e-6), 0, 1)
    r = (norm * 50).astype(np.uint8)
    g = (norm * 180).astype(np.uint8)
    b = (norm * 255).astype(np.uint8)
    return np.stack([r, g, b], axis=2)
