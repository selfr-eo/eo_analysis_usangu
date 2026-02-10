import geopandas as gpd
import pandas as pd
import earthaccess
import xarray as xr
import numpy as np
import os
import swot_download_tools as sdt



########### ----------------------- USER INPUT ----------------------- ###########

# Download parameters
temporal_range = ('2023-06-26 00:00:00', '2026-01-19 23:59:59')
product_id = 'SWOT_L2_HR_PIXC_D'  # SWOT_L2_HR_PIXC_2.0 for version C, SWOT_L2_HR_PIXC_D for version D - not available on earthdata search as of Dec 1 2025 for some reason??
classes = ['open_water','water_near_land']  # options: 'land', 'land_near_water', 'water_near_land', 'open_water', 'dark_water', 'low_coh_water_near_land', 'open_low_coh_water'
redownload_flag = False  # set to True to redownload files even if they already exist in the download path

# Paths
shapefile_path = "C:\\Users\\safr\\Documents\\test_altimetry_project\\shapefiles\\wetland_fans_domain_37S.shp"
download_path = "C:\\Users\\safr\\Documents\\test_altimetry_project\\data\\swot\\PIXC\\"


########### ----------------------- Download pixc data, trim, save to folder ----------------------- ###########


wetland_utm = gpd.read_file(shapefile_path)
wetland_ll = wetland_utm.to_crs("EPSG:4326")

auth = earthaccess.login() 
bbox = wetland_ll.total_bounds
results = earthaccess.search_data(short_name = product_id, 
                                  temporal = temporal_range,
                                   bounding_box = tuple(bbox) 
                                  )

granule_list = list(results)
print(f"Total granules found: {len(granule_list)}")

sdt.download_granule_list(granule_list, download_path, aoi=wetland_ll, classes=classes, redownload=redownload_flag)