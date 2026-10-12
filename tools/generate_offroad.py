import numpy as np
from PIL import Image, ImageFilter
from pathlib import Path

# Paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "worlds" / "heightmaps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Heightmap resolution: 2^n + 1 
N = 513

# Fixed seed so terrain stays the same every time
rng = np.random.default_rng(2909)

x = np.linspace(-1, 1, N)
y = np.linspace(-1, 1, N)
X, Y = np.meshgrid(x, y)

# BASE TERRAIN

# Flat quarry floor
terrain = np.full((N, N), 0.34, dtype=float)

# Very small natural ground variation
coarse = rng.normal(0, 1, (49, 49))
coarse = (coarse - coarse.min()) / (coarse.max() - coarse.min())
coarse_img = Image.fromarray(
    (coarse * 255).astype(np.uint8)
)

coarse_img = coarse_img.resize(
    (N, N),
    Image.Resampling.BICUBIC
)

terrain += (
    np.asarray(coarse_img, dtype=float) / 255.0 - 0.5
) * 0.018

# 1) LARGE OPEN WORKING FLOOR

work_area = np.exp(
    -(
        ((X + 0.02) / 0.68) ** 12
        + ((Y + 0.10) / 0.60) ** 12
    )
)

terrain = (
    terrain * (1 - 0.92 * work_area)
    + 0.34 * (0.92 * work_area)
)

# 2) STRONG QUARRY BENCHES

wall_shape = (
    0.018 * np.sin(2.5 * np.pi * X)
    + 0.008 * np.sin(6 * np.pi * X)
)

def quarry_step(y_position, width=0.010):
    return 0.5 * (
        1.0
        + np.tanh(
            (Y - (y_position + wall_shape)) / width
        )
    )

# Larger, clearer bench levels
terrain += 0.10 * quarry_step(0.32)
terrain += 0.11 * quarry_step(0.47)
terrain += 0.12 * quarry_step(0.62)
terrain += 0.13 * quarry_step(0.77)

# 4) SIDE QUARRY WALLS

left_wall = np.exp(
    -((X + 0.92) / 0.13) ** 4
) * np.exp(
    -((Y - 0.18) / 0.75) ** 8
)

right_wall = np.exp(
    -((X - 0.92) / 0.13) ** 4
) * np.exp(
    -((Y - 0.18) / 0.75) ** 8
)

terrain += 0.20 * left_wall
terrain += 0.20 * right_wall

# 5) WIDE HAUL / ACCESS RAMP

x1, y1 = 0.70, -0.90
x2, y2 = 0.73, 0.52

vx = x2 - x1
vy = y2 - y1

t = (
    (X - x1) * vx
    + (Y - y1) * vy
) / (vx * vx + vy * vy)

tc = np.clip(t, 0, 1)

px = x1 + tc * vx
py = y1 + tc * vy

distance = np.sqrt(
    (X - px) ** 2
    + (Y - py) ** 2
)

ramp_mask = (
    np.exp(-((distance / 0.13) ** 8))
    * ((t >= 0) & (t <= 1))
)

# Ramp gradually rises toward rear wall
ramp_height = 0.34 + 0.24 * tc

terrain = (
    terrain * (1 - 0.90 * ramp_mask)
    + ramp_height * (0.90 * ramp_mask)
)

# 6) RUBBLE / SPOIL RIDGE

# Irregular excavated rock material near the back-right.

spoil_zone = (
    np.exp(-((X - 0.28) / 0.40) ** 4)
    * np.exp(-((Y - 0.35) / 0.17) ** 4)
)

spoil_noise = (
    0.035 * np.sin(12 * np.pi * X)
    + 0.025 * np.sin(17 * np.pi * Y)
    + 0.018 * np.sin(9 * np.pi * (X + Y))
)

terrain += spoil_zone * (0.07 + spoil_noise)

piles = [
    (-0.58, -0.38, 0.10, 0.085, 0.070),
    (-0.18, -0.20, 0.08, 0.075, 0.060),
    ( 0.30, -0.38, 0.11, 0.090, 0.070),
    ( 0.48, -0.02, 0.09, 0.080, 0.065),
    (-0.43,  0.07, 0.08, 0.075, 0.060),
]

for cx, cy, amplitude, sx, sy in piles:

    mound = np.exp(
        -(
            ((X - cx) / sx) ** 2
            + ((Y - cy) / sy) ** 2
        ) * 1.8
    )

    terrain += amplitude * mound

# 8) ROCKY SURFACE ROUGHNESS

roughness = rng.normal(
    0,
    0.004,
    (N, N)
)

terrain += roughness * (1 - 0.80 * work_area)

terrain = np.clip(
    terrain,
    0.08,
    0.92
)

heightmap = (
    terrain * 255
).astype(np.uint8)

heightmap_path = (
    OUTPUT_DIR
    / "goose_construction_heightmap.png"
)

Image.fromarray(
    heightmap,
    mode="L"
).save(heightmap_path)

# ROCK / DIRT DIFFUSE TEXTURE

texture_size = 512

noise = rng.normal(
    0,
    1,
    (texture_size, texture_size)
)

noise = (
    noise - noise.min()
) / (
    noise.max() - noise.min()
)

noise_img = Image.fromarray(
    (noise * 255).astype(np.uint8)
)

noise_img = noise_img.filter(
    ImageFilter.GaussianBlur(radius=1.2)
)

n = (
    np.asarray(
        noise_img,
        dtype=float
    ) / 255.0
)

rgb = np.zeros(
    (texture_size, texture_size, 3),
    dtype=np.uint8
)

rgb[..., 0] = np.clip(
    105 + (n - 0.5) * 48,
    0,
    255
)

rgb[..., 1] = np.clip(
    96 + (n - 0.5) * 44,
    0,
    255
)

rgb[..., 2] = np.clip(
    82 + (n - 0.5) * 40,
    0,
    255
)

diffuse_path = (
    OUTPUT_DIR
    / "goose_construction_diffuse.png"
)

Image.fromarray(
    rgb,
    mode="RGB"
).save(diffuse_path)

# NORMAL MAP

normal = np.zeros(
    (texture_size, texture_size, 3),
    dtype=np.uint8
)

normal[..., 0] = 128
normal[..., 1] = 128
normal[..., 2] = 255

normal_path = (
    OUTPUT_DIR
    / "goose_construction_normal.png"
)

Image.fromarray(
    normal,
    mode="RGB"
).save(normal_path)

print("Construction environment resources generated:")
print(" -", heightmap_path)
print(" -", diffuse_path)
print(" -", normal_path)