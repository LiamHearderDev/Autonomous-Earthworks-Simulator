import numpy as np
from PIL import Image, ImageFilter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "worlds" / "heightmaps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N = 513

rng = np.random.default_rng(3009)

x = np.linspace(-1, 1, N)
y = np.linspace(-1, 1, N)

X, Y = np.meshgrid(x, y)

terrain = np.full((N, N), 0.42, dtype=float)

# 1. LARGE-SCALE NATURAL TERRAIN VARIATION

coarse = rng.normal(0, 1, (35, 35))
coarse = (coarse - coarse.min()) / (coarse.max() - coarse.min())
coarse_img = Image.fromarray((coarse * 255).astype(np.uint8))
coarse_img = coarse_img.resize((N, N),Image.Resampling.BICUBIC)
coarse_height = (np.asarray(coarse_img, dtype=float) / 255.0)

terrain += (coarse_height - 0.5) * 0.10

# 2. GENTLE FOREST HILLS

hills = [
    (-0.72,  0.45, 0.10, 0.38, 0.34),
    ( 0.72,  0.50, 0.12, 0.36, 0.30),
    (-0.72, -0.50, 0.08, 0.32, 0.30),
    ( 0.75, -0.42, 0.09, 0.34, 0.30),
]

for cx, cy, amplitude, sx, sy in hills:

    hill = np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2) * 1.25)
    terrain += amplitude * hill

# 3. MACHINE TRAIL

trail_centre = (0.10 * np.sin(1.6 * np.pi * Y) + 0.04 * np.sin(3.2 * np.pi * Y))
trail_distance = X - trail_centre
trail_mask = np.exp(-((trail_distance / 0.23) ** 8))
trail_target = (0.40+ 0.025 * Y+ 0.008 * np.sin(4 * np.pi * Y))

terrain = (terrain * (1 - 0.88 * trail_mask)+ trail_target * (0.88 * trail_mask))

# 4. TURNING AREA

work_area = np.exp(-(((X + 0.03) / 0.38) ** 10+ ((Y + 0.05) / 0.27) ** 10))

terrain = (terrain * (1 - 0.90 * work_area) + 0.40 * (0.90 * work_area))

# 5. FOREST FLOOR HUMMOCKS

hummocks = [
    (-0.55,  0.15, 0.045, 0.12, 0.10),
    (-0.68, -0.20, 0.050, 0.11, 0.09),
    ( 0.55,  0.20, 0.042, 0.12, 0.10),
    ( 0.67, -0.15, 0.052, 0.10, 0.09),
    (-0.48,  0.60, 0.040, 0.11, 0.10),
    ( 0.52, -0.62, 0.045, 0.11, 0.10),
]

for cx, cy, amplitude, sx, sy in hummocks:
    mound = np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2) * 1.8)
    terrain += amplitude * mound

# 6. SHALLOW NATURAL DIPS

dips = [(-0.62,  0.48, 0.035, 0.16, 0.13),( 0.60, -0.48, 0.030, 0.15, 0.12),]

for cx, cy, amplitude, sx, sy in dips:
    dip = np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2) * 1.6)
    terrain -= amplitude * dip

# 7. SMALL NATURAL ROUGHNESS

roughness = rng.normal(0, 0.0035, (N, N))

terrain += (roughness * (1 - 0.88 * trail_mask) * (1 - 0.80 * work_area))
terrain = np.clip(terrain, 0.12, 0.88)

# 8. DEFORMABLE TERRAIN RESERVE

dig_center_x = 0.0
dig_center_y = -0.20
dig_half_size = 0.06

dig_zone = (
    (np.abs(X - dig_center_x) <= dig_half_size)
    & (np.abs(Y - dig_center_y) <= dig_half_size)
)

terrain[dig_zone] = 0.0

heightmap = (terrain * 255).astype(np.uint8)
heightmap_path = (OUTPUT_DIR/ "goose_forest_heightmap.png")
Image.fromarray(heightmap,mode="L").save(heightmap_path)

texture_size = 512

noise = rng.normal(0,1,(texture_size, texture_size))
noise = (noise - noise.min()) / (noise.max() - noise.min())
noise_img = Image.fromarray((noise * 255).astype(np.uint8))
noise_img = noise_img.filter(ImageFilter.GaussianBlur(radius=1.3))

n = (np.asarray(noise_img,dtype=float) / 255.0)

broad_noise = rng.normal(0,1,(32, 32))
broad_noise = (broad_noise - broad_noise.min()) / (broad_noise.max() - broad_noise.min())
broad_img = Image.fromarray((broad_noise * 255).astype(np.uint8))
broad_img = broad_img.resize((texture_size, texture_size),Image.Resampling.BICUBIC)

b = (np.asarray(broad_img,dtype=float) / 255.0)

# FOREST FLOOR + VISIBLE DIRT TRAIL

tx = np.linspace(-1, 1, texture_size)
ty = np.linspace(-1, 1, texture_size)
TX, TY = np.meshgrid(tx, ty)

trail_centre_tex = (
    0.10 * np.sin(1.6 * np.pi * TY)
    + 0.04 * np.sin(3.2 * np.pi * TY)
)

trail_distance_tex = TX - trail_centre_tex

trail_texture_mask = np.exp(
    -((trail_distance_tex / 0.25) ** 8)
)

work_texture_mask = np.exp(
    -(
        ((TX + 0.03) / 0.38) ** 10
        + ((TY + 0.05) / 0.27) ** 10
    )
)

dirt_mask = np.maximum(
    trail_texture_mask,
    work_texture_mask
)

# FOREST / GRASS COLOUR

forest_r = np.clip(
    72
    + (n - 0.5) * 28
    + (b - 0.5) * 18,
    0,
    255
)

forest_g = np.clip(
    92
    + (n - 0.5) * 34
    + (b - 0.5) * 28,
    0,
    255
)

forest_b = np.clip(
    48
    + (n - 0.5) * 22
    + (b - 0.5) * 14,
    0,
    255
)

# DIRT ROAD COLOUR

dirt_r = np.clip(
    125
    + (n - 0.5) * 40,
    0,
    255
)

dirt_g = np.clip(
    94
    + (n - 0.5) * 34,
    0,
    255
)

dirt_b = np.clip(
    58
    + (n - 0.5) * 28,
    0,
    255
)

# BLEND FOREST AND DIRT

rgb = np.zeros(
    (texture_size, texture_size, 3),
    dtype=np.uint8
)

rgb[..., 0] = (
    forest_r * (1 - dirt_mask)
    + dirt_r * dirt_mask
).astype(np.uint8)

rgb[..., 1] = (
    forest_g * (1 - dirt_mask)
    + dirt_g * dirt_mask
).astype(np.uint8)

rgb[..., 2] = (
    forest_b * (1 - dirt_mask)
    + dirt_b * dirt_mask
).astype(np.uint8)

diffuse_path = (
    OUTPUT_DIR
    / "goose_forest_diffuse.png"
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
    / "goose_forest_normal.png"
)

Image.fromarray(
    normal,
    mode="RGB"
).save(normal_path)

print("GOOSE-inspired forest resources generated:")

print(" -", heightmap_path)
print(" -", diffuse_path)
print(" -", normal_path)