import numpy as np
from PIL import Image, ImageFilter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "worlds" / "heightmaps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N = 513
rng = np.random.default_rng(1509)

x = np.linspace(-1, 1, N)
y = np.linspace(-1, 1, N)
X, Y = np.meshgrid(x, y)

terrain = np.full((N, N), 0.50, dtype=float)

# gentle broad variation
coarse = rng.normal(0, 1, (49, 49))
coarse = (coarse - coarse.min()) / (coarse.max() - coarse.min())
coarse_img = Image.fromarray((coarse * 255).astype(np.uint8))
coarse_img = coarse_img.resize((N, N), Image.Resampling.BICUBIC)
terrain += (np.asarray(coarse_img, dtype=float) / 255.0 - 0.5) * 0.018

# 1) large flat central work pad
pad = np.exp(-(((X + 0.03) / 0.50) ** 10 + ((Y + 0.03) / 0.36) ** 10))
terrain = terrain * (1 - 0.96 * pad) + 0.50 * (0.96 * pad)

# 2) clear excavation pit
pit_cx, pit_cy = 0.40, 0.40
pit_rx, pit_ry = 0.34, 0.27
r2 = ((X - pit_cx) / pit_rx) ** 2 + ((Y - pit_cy) / pit_ry) ** 2
pit_core = np.exp(-(r2 / 0.72) ** 4)
terrain -= 0.30 * pit_core

# pit bench / lip
ring = np.exp(-((np.sqrt(r2) - 1.00) / 0.075) ** 2)
terrain += 0.095 * ring

# 3) wider, clearer haul ramp
x1, y1 = 0.74, -0.62
x2, y2 = 0.52, 0.17
vx, vy = x2 - x1, y2 - y1
t = ((X - x1) * vx + (Y - y1) * vy) / (vx * vx + vy * vy)
tc = np.clip(t, 0, 1)

px = x1 + tc * vx
py = y1 + tc * vy
dist = np.sqrt((X - px) ** 2 + (Y - py) ** 2)

ramp_mask = np.exp(-((dist / 0.145) ** 6)) * ((t >= 0) & (t <= 1))
ramp_target = 0.50 - 0.25 * tc
terrain = terrain * (1 - 0.98 * ramp_mask) + ramp_target * (0.98 * ramp_mask)

shoulders = np.exp(-(((dist - 0.17) / 0.035) ** 2)) * ((t >= 0) & (t <= 1))
terrain += 0.035 * shoulders

# 4) perimeter bund with south opening
edge = np.minimum.reduce([X + 1, 1 - X, Y + 1, 1 - Y])
bund = np.exp(-((edge - 0.075) / 0.038) ** 2)
opening = np.exp(-((X / 0.25) ** 2 + ((Y + 0.96) / 0.08) ** 2))
terrain += 0.19 * bund * (1 - 0.99 * opening)

# 5) three visible stockpiles
piles = [
    (-0.50, 0.36, 0.27, 0.11, 0.09),
    (-0.30, 0.39, 0.23, 0.105, 0.085),
    (-0.10, 0.36, 0.20, 0.095, 0.078),
]
for cx, cy, amplitude, sx, sy in piles:
    mound = np.exp(-((((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2) * 1.65))
    terrain += amplitude * mound

# 6) rough off-road lane
lane = (
    np.exp(-((X + 0.64) / 0.17) ** 12)
    * np.exp(-((Y + 0.12) / 0.58) ** 12)
)
waves = (
    0.065 * np.sin(8 * np.pi * (Y + 0.18))
    + 0.022 * np.sin(5 * np.pi * Y + 3 * np.pi * X)
)
terrain += lane * waves

# 7) shallow trench
trench = np.exp(-((((X + 0.25) / 0.24) ** 2 + ((Y + 0.55) / 0.075) ** 2) * 2.0))
terrain -= 0.09 * trench

# 8) small roughness outside work pad and ramp
terrain += (
    rng.normal(0, 0.0028, (N, N))
    * (1 - 0.97 * pad)
    * (1 - 0.92 * ramp_mask)
)

terrain = np.clip(terrain, 0.10, 0.88)
heightmap = (terrain * 255).astype(np.uint8)

Image.fromarray(heightmap, mode="L").save(
    OUTPUT_DIR / "aarp_goose_demo_heightmap_v2.png"
)

# dirt diffuse texture
texture_size = 512
noise = rng.normal(0, 1, (texture_size, texture_size))
noise = (noise - noise.min()) / (noise.max() - noise.min())
noise_img = Image.fromarray((noise * 255).astype(np.uint8))
noise_img = noise_img.filter(ImageFilter.GaussianBlur(radius=1.4))
n = np.asarray(noise_img, dtype=float) / 255.0

rgb = np.zeros((texture_size, texture_size, 3), dtype=np.uint8)
rgb[..., 0] = np.clip(158 + (n - 0.5) * 36, 0, 255)
rgb[..., 1] = np.clip(119 + (n - 0.5) * 30, 0, 255)
rgb[..., 2] = np.clip(66 + (n - 0.5) * 24, 0, 255)

Image.fromarray(rgb, mode="RGB").save(OUTPUT_DIR / "dirt_diffuse_v2.png")

# neutral flat normal
normal = np.zeros((texture_size, texture_size, 3), dtype=np.uint8)
normal[..., 0] = 128
normal[..., 1] = 128
normal[..., 2] = 255

Image.fromarray(normal, mode="RGB").save(OUTPUT_DIR / "flat_normal.png")

print("Generated / updated in:", OUTPUT_DIR)
print(" - aarp_goose_demo_heightmap_v2.png")
print(" - dirt_diffuse_v2.png")
print(" - flat_normal.png")