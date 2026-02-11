
import glob
import os
import sys
import datetime
from tqdm import tqdm
import geopandas as gpd
import eo_tools as eot

# loop though daily trimmed files, plot histograms for each, create rasters for each at specified resolution


########### ----------------------- USER INPUT ----------------------- ###########
selField = 'water_frac'  # or 'heightEGM', 'phase_noise_std', 'dheight_dphase'
selMetric = 'median'  # or 'mean', 'max', etc.
trimmed_filelist = glob.glob("C:\\Users\\safr\\Documents\\test_altimetry_project\\data\\swot\\PIXC\\*_trimmed.geojson")

outdir = "C:\\Users\\safr\\Documents\\test_altimetry_project\\data\\swot\\processed\\"
if not os.path.exists(outdir):
    os.makedirs(outdir)

swot_raster_dir = outdir+"raster\\"
if not os.path.exists(swot_raster_dir):
    os.makedirs(swot_raster_dir)

hist_dir = outdir+"histograms\\"
if not os.path.exists(hist_dir):
    os.makedirs(hist_dir)
########### ----------------------- Process pixc data to gridded raster ----------------------- ###########


wetland_utm = gpd.read_file("C:\\Users\\safr\\Documents\\test_altimetry_project\\shapefiles\\wetland_fans_domain_37S.shp")
wetland_ll = wetland_utm.to_crs("EPSG:4326")

grid_size = 100  # in meters

# delete files from os that are less than 10 KB
for file in trimmed_filelist:
    if os.path.getsize(file) < 10000:
        print(f"file size: {os.path.getsize(file)} bytes")
        os.remove(file)
        print(f"Deleted empty file: {file}")

unique_dates = set()
for trimmed_file in trimmed_filelist:
    # check file size - skip if 0 bytes
    if os.path.getsize(trimmed_file) < 10000:  # less than 10 KB
        print(f"Skipping empty file: {trimmed_file}")
        continue

    str_date = os.path.basename(trimmed_file).split("_")[-4]

    # check if raster has already been processed for this date
    raster_date = str_date[0:4] + "-" + str_date[4:6] + "-" + str_date[6:8]
    raster_filename = swot_raster_dir+f"{raster_date}_res{grid_size}_{selField}.tif"
    if os.path.exists(raster_filename):
        print(f"Raster already exists for date {raster_date}, skipping processing.")
        continue

    # parse yyyymmddThhmmss to datetime
    t = datetime.datetime.strptime(str_date, "%Y%m%dT%H%M%S")
    unique_dates.add(t.date())

for date in tqdm(sorted(unique_dates), desc="Processing dates"):
    # Print current date being processed, with tqdm progress bar
    tqdm.write(f"Processing date: {date.strftime('%Y-%m-%d')}")

    ########### Load data for this date
    filenames_for_date = [f for f in trimmed_filelist if date.strftime("%Y%m%d") in f]
    gdf_date = eot.load_trimmed_pixc_data(filenames_for_date)
    # for raster creation
    gdf_date_utm = gdf_date.to_crs(wetland_utm.crs)

    ########## Plot histogram of heights for this date and plot location map, save to file
    eot.plot_hist_map(gdf_date, field=selField, shapefile_ll=wetland_ll, date=date, outdir=hist_dir)

    ########### Create raster for this date at specified resolution
    stat_raster = eot.grid_sampling(
        shapefile_utm=wetland_utm,
        gdf_points=gdf_date_utm,
        buffer=0.01,
        field=selField,
        stat_method=selMetric,
        grid_resolution=grid_size,
        filedate=str(date)+'_res'+str(grid_size),
        plotFlag=False,
        countFlag=False,
        writeGeoTIFF=True,
        swot_raster_dir=swot_raster_dir
    )