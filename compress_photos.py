"""
Compress JPGs in photos/ for web delivery.
- Max dimension: 1920px (preserves aspect ratio)
- JPEG quality: 82 (visually lossless for photographic content)
- Progressive: True (faster perceived load)
- Strips EXIF metadata
- Overwrites in place (originals are tracked in git)
"""
import os
from PIL import Image, ImageOps

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "photos")
MAX_DIM = 1920
QUALITY = 82
SKIP_BELOW_KB = 200  # don't bother compressing already-small files

def fmt_size(bytes_val):
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024*1024):.2f} MB"
    return f"{bytes_val / 1024:.0f} KB"

def process(path):
    before = os.path.getsize(path)
    if before < SKIP_BELOW_KB * 1024:
        return (path, before, before, "skipped (already small)")

    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)  # respect EXIF orientation, then strip
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        w, h = img.size
        if max(w, h) > MAX_DIM:
            if w >= h:
                new_w = MAX_DIM
                new_h = round(h * MAX_DIM / w)
            else:
                new_h = MAX_DIM
                new_w = round(w * MAX_DIM / h)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        # Save with optimization
        img.save(
            path,
            "JPEG",
            quality=QUALITY,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
        )
        after = os.path.getsize(path)
        return (path, before, after, f"{img.size[0]}x{img.size[1]}")
    except Exception as e:
        return (path, before, before, f"ERROR: {e}")

def main():
    files = sorted(
        f for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith((".jpg", ".jpeg"))
    )
    total_before = 0
    total_after = 0
    print(f"{'file':<35} {'before':>10} {'after':>10} {'saved':>10}  info")
    print("-" * 90)
    for f in files:
        path = os.path.join(PHOTOS_DIR, f)
        _, before, after, info = process(path)
        total_before += before
        total_after += after
        saved_pct = (1 - after / before) * 100 if before else 0
        print(f"{f:<35} {fmt_size(before):>10} {fmt_size(after):>10} {saved_pct:>8.1f}%  {info}")
    print("-" * 90)
    saved_total_pct = (1 - total_after / total_before) * 100 if total_before else 0
    print(f"{'TOTAL':<35} {fmt_size(total_before):>10} {fmt_size(total_after):>10} {saved_total_pct:>8.1f}%")

if __name__ == "__main__":
    main()
