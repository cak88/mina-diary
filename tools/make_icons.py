"""ドット絵(24×24)のアイコンを assets/ に書く。外部依存なし。
- mina-*.png: ミナの差分。地('.')は透明
- cak.png: 引用の話者の cak。Cosense の cak のアイコン(水色の部屋の隅)をドット絵にしたもの

使い方: python3 tools/make_icons.py
"""

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASE = """
........................
.........GG..GG.........
..........GggG..........
........yYYggYYy........
.......yYYYYYYYYYy......
.......RRRRRRRRRR.......
..yYYYYYYYYYYYYYYYYYYy..
...yyyyyyyyyyyyyyyyyy...
......KBBBBBBBBBBK......
.....KBBBBBBBBBBBBK..M..
.....KBBEWBBBBEWBBK.MMM.
....KBBBEEBBBBEEBBBKMMm.
....KBCCBBBLLBBBCCBK.m..
....KBCCBBLPPLBBCCBK.H..
....KBBBBBLPPLBBBBBK.H..
....KBBBBBBLLBBBBBBK.H..
...sKBPPPBBBBBBBBBKPPP..
..sSKPPPPPBBBBBBBBKPPPs.
.sSSSSPPPSSSSSSSSSSSSSs.
sSSSSSSSSSSSSSSSSSSSSSSs
SSSsSSSSSSsSSSSSSSsSSSSS
SSSSSSSsSSSSSSSsSSSSSSSS
SSsSSSSSSSSSSsSSSSSSSsSS
SSSSSSSSSSSSSSSSSSSSSSSS
""".strip().splitlines()

PAL = {
    "K": (0x3B, 0x2A, 0x24), "B": (0x6B, 0x50, 0x48), "L": (0x8F, 0x72, 0x67), "P": (0xE8, 0x9A, 0xA6),
    "E": (0x1C, 0x14, 0x12), "W": (0xFF, 0xFF, 0xFF), "G": (0x6A, 0xB0, 0x52), "g": (0x3D, 0x7A, 0x33),
    "S": (0xA0, 0x72, 0x4A), "s": (0x7A, 0x52, 0x35), "C": (0xD9, 0x8A, 0x93), "Y": (0xE8, 0xC4, 0x6A),
    "y": (0xB8, 0x91, 0x3F), "R": (0x4F, 0x8F, 0x3E), "M": (0xB4, 0xBC, 0xC4), "m": (0x6B, 0x74, 0x80),
    "H": (0x8A, 0x5A, 0x2B), "h": (0xE3, 0x70, 0xA9),
}


def put(grid, cells):
    g = [list(r) for r in grid]
    for (r, c), v in cells.items():
        g[r][c] = v
    return ["".join(r) for r in g]


def close_eyes(grid, left=True, right=True):
    cells = {}
    for c0, on in ((8, left), (14, right)):
        if on:
            cells.update({(10, c0): "B", (10, c0 + 1): "B", (11, c0): "E", (11, c0 + 1): "E"})
    return put(grid, cells)


NO_TROWEL = {(9, 21): ".", (10, 20): ".", (10, 21): ".", (10, 22): ".", (11, 20): ".", (11, 21): ".",
             (11, 22): ".", (12, 21): ".", (13, 21): ".", (14, 21): ".", (15, 21): "."}

VARIANTS = {
    "clear": BASE,
    "flip": [r[::-1] for r in BASE],
    "wink": close_eyes(BASE, left=False),
    "sleep": put(close_eyes(BASE), {(1, 18): "K", (1, 19): "K", (1, 20): "K", (2, 19): "K",
                                    (3, 18): "K", (3, 19): "K", (3, 20): "K"}),
    "sprout": put(BASE, {**NO_TROWEL, (9, 20): "G", (9, 22): "g", (10, 20): "G", (10, 21): "g", (10, 22): "g",
                         **{(r, 21): "g" for r in range(11, 16)}}),
    "heart": put(BASE, {(1, 18): "h", (1, 19): "h", (1, 21): "h", (1, 22): "h",
                        **{(2, c): "h" for c in range(18, 23)}, (3, 19): "h", (3, 20): "h", (3, 21): "h",
                        (4, 20): "h"}),
}


def png(grid, scale=4):
    raw = b""
    for r in grid:
        line = b"".join(
            (b"\x00\x00\x00\x00" if ch == "." else bytes(PAL[ch]) + b"\xff") for ch in r for _ in range(scale)
        )
        raw += (b"\x00" + line) * scale

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    w, h = len(grid[0]) * scale, len(grid) * scale
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# cak の部屋の隅: 奥の角(12,13)から、縦の稜線が上へ、床の稜線が左下(0,19)と右下(24,19)へ伸びる。
# 面ごとに上ほど明るい2〜3段の水色にし、稜線は1段明るくする。
CAK_PAL = {
    "1": (0xC6, 0xEA, 0xFB), "2": (0x9F, 0xD8, 0xF7), "3": (0x6F, 0xC0, 0xF0),  # 左の壁
    "4": (0xD5, 0xF0, 0xFC), "5": (0xAE, 0xDF, 0xF8), "6": (0x82, 0xCA, 0xF2),  # 右の壁
    "7": (0x86, 0xCF, 0xF6), "8": (0x74, 0xC6, 0xF4),                          # 床
    "9": (0xE6, 0xF6, 0xFE),                                                  # 稜線
}


def cak_grid():
    cx, cy = 12, 13
    rows = []
    for y in range(24):
        row = ""
        for x in range(24):
            px, py = x + 0.5, y + 0.5
            yl = cy + (cx - px) * (19 - cy) / cx      # 左の床の稜線の高さ
            yr = cy + (px - cx) * (19 - cy) / (24 - cx)  # 右の床の稜線の高さ
            floor_edge = yl if px < cx else yr
            if abs(py - floor_edge) < 0.55 and py >= cy - 0.5:
                row += "9"
            elif py > floor_edge:
                row += "8" if py > 21 else "7"
            elif abs(px - cx) < 0.55:
                row += "9"
            elif px < cx:
                row += "1" if py < 6 else "2" if py < 13 else "3"
            else:
                row += "4" if py < 6 else "5" if py < 13 else "6"
        rows.append(row)
    return rows


def main():
    items = {f"mina-{k}": v for k, v in VARIANTS.items()}
    items["cak"] = cak_grid()
    assert not set(CAK_PAL) & set(PAL), "記号がぶつかっている"
    PAL.update(CAK_PAL)
    for name, grid in items.items():
        assert len(grid) == 24 and all(len(r) == 24 for r in grid), name
        (ROOT / "assets" / f"{name}.png").write_bytes(png(grid))
        print(f"assets/{name}.png")


if __name__ == "__main__":
    main()
