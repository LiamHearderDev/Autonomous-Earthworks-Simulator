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

terrain = np.full((N, N), 0.48, dtype=float)

# 1. BROAD VARIATION

coarse = rng.normal(0, 1, (49, 49))
coarse = (coarse - coarse.min()) / (coarse.max() - coarse.min())
coarse_img = Image.fromarray((coarse * 255).astype(np.uint8))
coarse_img = coarse_img.resize((N, N), Image.Resampling.BICUBIC)
terrain += (np.asarray(coarse_img, dtype=float) / 255.0 - 0.5) * 0.015

# 2. MAIN FLAT TEST PAD - LARGE

main_pad = np.exp(
    -(
        ((X - 0.02) / 0.58) ** 10
        + ((Y + 0.02) / 0.42) ** 10
    )
)
terrain = terrain * (1 - 0.97 * main_pad) + 0.49 * (0.97 * main_pad)

# 3. SECONDARY FLAT WORK PAD

secondary_pad = np.exp(
    -(
        ((X + 0.58) / 0.22) ** 10
        + ((Y - 0.10) / 0.18) ** 10
    )
)
terrain = terrain * (1 - 0.95 * secondary_pad) + 0.48 * (0.95 * secondary_pad)

# 4. HAUL ROAD

road = (
    np.exp(-((X + 0.05) / 0.18) ** 12)
    * np.exp(-((Y + 0.15) / 0.80) ** 12)
)
road_target = 0.47 + 0.01 * np.sin(2 * np.pi * Y)
terrain = terrain * (1 - 0.92 * road) + road_target * (0.92 * road)

road_shoulders = (
    np.exp(-(((np.abs(X + 0.05) - 0.20) / 0.035) ** 2))
    * np.exp(-((Y + 0.15) / 0.80) ** 12)
)
terrain += 0.018 * road_shoulders

aarp_pad = np.exp(
    -(
        ((X + 0.02) / 0.62) ** 16
        + ((Y + 0.02) / 0.43) ** 16
    )
)

terrain = terrain * (1 - 0.94 * aarp_pad) + 0.49 * (0.94 * aarp_pad)

outer_rect = np.exp(
    -(
        ((X + 0.02) / 0.69) ** 18
        + ((Y + 0.02) / 0.50) ** 18
    )
)

inner_rect = np.exp(
    -(
        ((X + 0.02) / 0.61) ** 18
        + ((Y + 0.02) / 0.42) ** 18
    )
)

test_bund = np.clip(outer_rect - inner_rect, 0, 1)
terrain += 0.075 * test_bund

haul_lane = (
    np.exp(-((X - 0.58) / 0.085) ** 10)
    * np.exp(-((Y + 0.02) / 0.78) ** 12)
)

terrain = (
    terrain * (1 - 0.90 * haul_lane)
    + 0.465 * (0.90 * haul_lane)
)

access_lane = (
    np.exp(-((Y + 0.58) / 0.075) ** 10)
    * np.exp(-((X + 0.02) / 0.80) ** 12)
)

terrain = (
    terrain * (1 - 0.90 * access_lane)
    + 0.465 * (0.90 * access_lane)
)

# 5. LOW PERIMETER BERMS

edge = np.minimum.reduce([X + 1, 1 - X, Y + 1, 1 - Y])
bund = np.exp(-((edge - 0.085) / 0.045) ** 2)

south_opening = np.exp(-((X / 0.28) ** 2 + ((Y + 0.96) / 0.10) ** 2))
east_opening = np.exp(-(((X - 0.96) / 0.08) ** 2 + ((Y - 0.05) / 0.22) ** 2))

terrain += 0.13 * bund * (1 - 0.98 * south_opening) * (1 - 0.95 * east_opening)

# 6. EARTH MOUNDS

piles = [
    (-0.70, 0.43, 0.24, 0.12, 0.10),
    (-0.48, 0.43, 0.20, 0.11, 0.09),
    (-0.27, 0.43, 0.17, 0.10, 0.085),
]

for cx, cy, amplitude, sx, sy in piles:
    mound = np.exp(-((((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2) * 1.8))
    terrain += amplitude * mound

# 7. LOW PLATFORM

raised_area = np.exp(
    -(
        ((X - 0.62) / 0.22) ** 8
        + ((Y - 0.52) / 0.16) ** 8
    )
)
terrain += 0.08 * raised_area

# 8. SCRAPE AREA

scrape = np.exp(
    -(
        ((X - 0.45) / 0.20) ** 2
        + ((Y + 0.35) / 0.11) ** 2
    ) * 1.8
)
terrain -= 0.05 * scrape

# 9. DIG HOLE 

dig_x_min = -0.06
dig_x_max =  0.06

dig_y_min = -0.26
dig_y_max = -0.14

dig_zone = (
    (X >= dig_x_min) & (X <= dig_x_max) &
    (Y >= dig_y_min) & (Y <= dig_y_max))

terrain[dig_zone] = 0.06

dig_zone_soft = np.exp(
    -(
        ((X - 0.0) / 0.075) ** 8
        + ((Y + 0.20) / 0.075) ** 8
    )
)
terrain = np.minimum(terrain, terrain * (1 - 0.35 * dig_zone_soft) + 0.08 * (0.35 * dig_zone_soft))

# 10. OUTER ROUGHNESS

terrain += (
    rng.normal(0, 0.003, (N, N))
    * (1 - 0.95 * main_pad)
    * (1 - 0.90 * secondary_pad)
    * (1 - 0.85 * road)
)

stockpiles = [
    (-0.55, 0.48, 0.18, 0.11, 0.09),
    (-0.35, 0.50, 0.15, 0.10, 0.085),
    (-0.17, 0.48, 0.12, 0.09, 0.075),
]

for cx, cy, amplitude, sx, sy in stockpiles:
    pile = np.exp(
        -(
            ((X - cx) / sx) ** 2
            + ((Y - cy) / sy) ** 2
        ) * 1.8
    )
    terrain += amplitude * pile

loading_ramp = np.exp(
    -(
        ((X - 0.55) / 0.18) ** 6
        + ((Y - 0.42) / 0.16) ** 6
    )
)

terrain += 0.10 * loading_ramp

terrain = np.clip(terrain, 0.04, 0.88)
heightmap = (terrain * 255).astype(np.uint8)

Image.fromarray(heightmap, mode="L").save(
    OUTPUT_DIR / "aarp_goose_demo_heightmap_v2.png"
)

# DIFFUSE TEXTURE

texture_size = 512

noise = rng.normal(0, 1, (texture_size, texture_size))
noise = (noise - noise.min()) / (noise.max() - noise.min())

noise_img = Image.fromarray((noise * 255).astype(np.uint8))
noise_img = noise_img.filter(ImageFilter.GaussianBlur(radius=2.0))

n = np.asarray(noise_img, dtype=float) / 255.0

broad_noise = rng.normal(0, 1, (32, 32))
broad_noise = (broad_noise - broad_noise.min()) / (
    broad_noise.max() - broad_noise.min()
)

broad_img = Image.fromarray(
    (broad_noise * 255).astype(np.uint8)
)

broad_img = broad_img.resize(
    (texture_size, texture_size),
    Image.Resampling.BICUBIC
)

b = np.asarray(broad_img, dtype=float) / 255.0

tx = np.linspace(-1, 1, texture_size)
ty = np.linspace(-1, 1, texture_size)
TX, TY = np.meshgrid(tx, ty)

track_a = (
    np.exp(-((TX + 0.14) / 0.018) ** 2)
    * np.exp(-((TY + 0.05) / 0.34) ** 8)
)

track_b = (
    np.exp(-((TX + 0.06) / 0.018) ** 2)
    * np.exp(-((TY + 0.05) / 0.34) ** 8)
)

track_mask = np.clip(track_a + track_b, 0, 1)

outer_road = (
    (np.abs(TX + 0.02) <= 0.72)
    & (np.abs(TY + 0.02) <= 0.54)
)

inner_road = (
    (np.abs(TX + 0.02) <= 0.58)
    & (np.abs(TY + 0.02) <= 0.40)
)

perimeter_road = outer_road & (~inner_road)

right_haul_road = (
    (np.abs(TX - 0.58) <= 0.09)
    & (np.abs(TY + 0.02) <= 0.78)
)

access_road = (
    (np.abs(TY + 0.58) <= 0.08)
    & (np.abs(TX + 0.02) <= 0.80)
)

road_mask = (
    perimeter_road
    | right_haul_road
    | access_road
).astype(float)

road_mask_img = Image.fromarray(
    (road_mask * 255).astype(np.uint8)
)

road_mask_img = road_mask_img.filter(
    ImageFilter.GaussianBlur(radius=3.0)
)

road_mask = (
    np.asarray(road_mask_img, dtype=float) / 255.0
)

sand_r = np.clip(
    166 + (n - 0.5) * 22 + (b - 0.5) * 12,
    0, 255
)

sand_g = np.clip(
    128 + (n - 0.5) * 18 + (b - 0.5) * 10,
    0, 255
)

sand_b = np.clip(
    78 + (n - 0.5) * 16 + (b - 0.5) * 8,
    0, 255
)

road_r = np.clip(
    118 + (n - 0.5) * 18,
    0, 255
)

road_g = np.clip(
    91 + (n - 0.5) * 15,
    0, 255
)

road_b = np.clip(
    58 + (n - 0.5) * 12,
    0, 255
)

rgb = np.zeros(
    (texture_size, texture_size, 3),
    dtype=np.uint8
)

rgb[..., 0] = (
    sand_r * (1 - road_mask)
    + road_r * road_mask
).astype(np.uint8)

rgb[..., 1] = (
    sand_g * (1 - road_mask)
    + road_g * road_mask
).astype(np.uint8)

rgb[..., 2] = (
    sand_b * (1 - road_mask)
    + road_b * road_mask
).astype(np.uint8)

rgb[..., 0] = (rgb[..., 0] * (1 - 0.18 * track_mask)).astype(np.uint8)
rgb[..., 1] = (rgb[..., 1] * (1 - 0.18 * track_mask)).astype(np.uint8)
rgb[..., 2] = (rgb[..., 2] * (1 - 0.18 * track_mask)).astype(np.uint8)

Image.fromarray(
    rgb,
    mode="RGB"
).save(
    OUTPUT_DIR / "dirt_diffuse_v2.png"
)

# NORMAL MAP

normal = np.zeros((texture_size, texture_size, 3), dtype=np.uint8)
normal[..., 0] = 128
normal[..., 1] = 128
normal[..., 2] = 255

Image.fromarray(normal, mode="RGB").save(OUTPUT_DIR / "flat_normal.png")

print("Generated / updated in:", OUTPUT_DIR)
print(" - aarp_goose_demo_heightmap_v2.png")
print(" - dirt_diffuse_v2.png")
print(" - flat_normal.png")