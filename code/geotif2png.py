
from PIL import Image,ImageSequence
import glob as glob
import os
from datetime import datetime
import rasterio
import numpy as np
from collections import defaultdict
import os
import glob


# Converts geotiffs to pngs and creates monthly median composites

def extract_year_month(fname):
    """
    Extract YYYY, MM from filenames like:
    S2_RGB_2021-01-28_b3.tif
    """
    try:
        date_str = fname.split('_')[2]  # '2021-01-28'
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.year, dt.month
    except Exception:
        return None, None


# For saving exported geotiffs as pngs
folder = ['b1','b2','b3','b4','b5','b6','b7','b8']
monthly_aggregate_flag = True
process_all_files_flag = False

if process_all_files_flag:
    for b in folder:
        folderpath = r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal\\" + b + "\\tif"
        print('Processing box: ' + b)
        # loop through all files and save .tif as .png
        for file in glob.glob(os.path.join(folderpath, "*.tif")):
            # Get the filename without the extension
            filename_ext = os.path.basename(file)
            filename = os.path.splitext(os.path.basename(file))[0]
            try:
                im = Image.open(file)
                for i, page in enumerate(ImageSequence.Iterator(im)):
                    path = r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal\\" + b + "\\" + filename + ".png"
                    if not os.path.isfile(path):
                        try:
                            page = page.resize((600,500))
                            print('Saving: ' + path)
                            page.save(path,"png",quality=100)
                        except:
                            print(filename_ext)
            except:
                print(filename_ext)

if monthly_aggregate_flag:

    for b in folder:
        folderpath = (
            r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal\\"
            + b + "\\tif"
        )

        outpath = (
            r"C:\Users\safr\Documents\github\eo_analysis_usangu\data\S2_temporal\\"
            + b + "\\monthly"
        )
        os.makedirs(outpath, exist_ok=True)

        print(f"\nProcessing monthly medians for box: {b}")

        # Group files by (year, month)
        monthly_files = defaultdict(list)

        for file in glob.glob(os.path.join(folderpath, "*.tif")):
            fname = os.path.basename(file)
            year, month = extract_year_month(fname)

            if year is None:
                continue

            if 2020 <= year <= 2025:
                monthly_files[(year, month)].append(file)

        # Loop through grouped months
        for (year, month), files in monthly_files.items():

            out_tif = os.path.join(
                outpath,
                f"S2_RGB_{year}-{month:02d}_median_{b}.tif"
            )

            if os.path.isfile(out_tif):
                print(f"  {b} {year}-{month:02d}: already exists, skipping")
                continue

            if len(files) == 0:
                continue

            print(f"  {b} {year}-{month:02d}: {len(files)} images")

            rgb_stack = []
            meta = None
            ref_shape = None

            for f in files:
                try:
                    with rasterio.open(f) as src:
                        data = src.read().astype(np.float32)

                        # Initialize reference shape
                        if ref_shape is None:
                            ref_shape = data.shape
                            meta = src.meta.copy()

                        # Skip mismatched shapes
                        if data.shape != ref_shape:
                            print(f"    Skipping (shape mismatch): {os.path.basename(f)} "
                                f"{data.shape} != {ref_shape}")
                            continue

                        rgb_stack.append(data)

                except Exception as e:
                    print(f"    Skipping (read error): {os.path.basename(f)}")
                    continue

            # Stack → (N, 3, H, W)
            rgb_stack = np.stack(rgb_stack, axis=0)

            # Median across time axis
            rgb_median = np.nanmedian(rgb_stack, axis=0)

            meta.update(
                dtype=rasterio.float32,
                count=3,
                compress="lzw"
            )

            out_tif = os.path.join(
                outpath,
                f"S2_RGB_{year}-{month:02d}_median_{b}.tif"
            )

            with rasterio.open(out_tif, "w", **meta) as dst:
                dst.write(rgb_median)

            print(f"    Saved: {out_tif}")

        # Convert monthly tifs to pngs
        monthly_tifs = glob.glob(os.path.join(outpath, "*.tif"))

        for file in monthly_tifs:
            filename = os.path.splitext(os.path.basename(file))[0]
            png_path = os.path.join(outpath, filename + ".png")
            print('Processing: ' + filename)

            if not os.path.isfile(png_path):
                with rasterio.open(file) as src:
                    rgb = src.read([1, 2, 3])

                    # Normalize to 0–255 for PNG
                    rgb = np.clip(rgb, 0, np.percentile(rgb, 99))
                    rgb = (rgb / rgb.max() * 255).astype(np.uint8)

                    img = Image.fromarray(np.transpose(rgb, (1, 2, 0)))
                    img.resize((600, 500)).save(png_path, "PNG")