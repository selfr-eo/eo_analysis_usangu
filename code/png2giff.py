# Generate gif from png files

from PIL import Image, ImageDraw, ImageFont
import glob
import os
from datetime import datetime
import pandas as pd

base_path = r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal"
folders = ['b1','b2','b3','b4','b5','b6','b7','b8']

font_path = r"C:\Windows\Fonts\arialbd.ttf"
font_size = 48

start_date = datetime(2020, 1, 1)
end_date   = datetime(2025, 12, 1)

frame_size = (600, 500)   # must match your PNG export

def extract_year_month(fname):
    for part in fname.split('_'):
        try:
            dt = datetime.strptime(part, "%Y-%m")
            return dt.year, dt.month
        except:
            continue
    return None, None


def draw_date_label(img, text, font, y_offset=20):
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (img.width - text_w) // 2
    y = y_offset

    # Optional semi-transparent background for readability
    pad = 8
    draw.rectangle(
        [x - pad, y - pad, x + text_w + pad, y + text_h + pad],
        fill=(0, 0, 0, 160)
    )

    draw.text(
        (x, y),
        text,
        fill=(255, 255, 255, 255),
        font=font
    )

    return img.convert("RGB")


def draw_no_data_label(img, font_path):

    font = ImageFont.truetype(font_path, 64)
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    text = "NO DATA"

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (img.width - text_w) // 2
    y = (img.height - text_h) // 2

    # Semi-transparent text
    draw.text((x, y), text, fill=(255,255,255,180),
          font=font, stroke_width=2, stroke_fill=(0,0,0,200))

    return img.convert("RGB")



timeline = pd.date_range(start=start_date, end=end_date, freq="MS")
font = ImageFont.truetype(font_path, font_size)

for b in folders:
    monthly_path = os.path.join(base_path, b, "monthly")
    pngs = glob.glob(os.path.join(monthly_path, "*.png"))

    if len(pngs) == 0:
        print(f"No monthly PNGs found for {b}, skipping.")
        continue

    # Build lookup: (year, month) → png
    png_lookup = {}
    for p in pngs:
        y, m = extract_year_month(os.path.basename(p))
        if y is not None:
            png_lookup[(y, m)] = p

    frames = []

    for dt in timeline:
        ym = (dt.year, dt.month)
        label = dt.strftime("%Y-%m")

        if ym in png_lookup:
            img = Image.open(png_lookup[ym]).resize(frame_size)
            img = draw_date_label(img, label, font)
        else:
            img = Image.new("RGB", frame_size, (0, 0, 0))
            img = draw_no_data_label(img, font_path)
            img = draw_date_label(img, label, font)

        frames.append(img)

    gif_path = os.path.join(monthly_path, f"{b}_monthly.gif")

    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=600,
        loop=0
    )

    print(f"Saved GIF with full timeline: {gif_path}")
