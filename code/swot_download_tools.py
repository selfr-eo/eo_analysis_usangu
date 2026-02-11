
import geopandas as gpd
import pandas as pd
import xarray as xr
import numpy as np
import earthaccess
import os



def translateClass(flag_meanings):

    class_dict = {
        'land':1,
        'land_near_water':2,
        'water_near_land':3,
        'open_water':4,
        'dark_water':5,
        'low_coh_water_near_land':6,
        'open_low_coh_water':7
    }
    flag_values = [class_dict[flag_meaning] for flag_meaning in flag_meanings]

    return flag_values
def readPIXC(filename: str, aoi: gpd.GeoDataFrame = None, classes=['open_water'], engine="netcdf4"):
    
    # If no centerline buffer to trim to, set gdf_buffered = []
    with xr.open_mfdataset(filename, group="pixel_cloud", engine=engine) as nc:
        
        # Set crs of nc file
        nc = nc.rio.write_crs("EPSG:4326", inplace=True)

        # select based on desired classification
        class_flat = nc.classification.values.ravel()
        flag_values = translateClass(classes)
        class_condition = np.isin(class_flat, flag_values)

        # Set the nc to a geopandas dataset
        class_flat = class_flat[class_condition]
        lon_flat = nc.longitude.values.ravel()[class_condition]
        lat_flat = nc.latitude.values.ravel()[class_condition]
        height = nc.height.values.ravel()[class_condition]
        geoid = nc.geoid.values.ravel()[class_condition]
        solid_earth_tide = nc.solid_earth_tide.values.ravel()[class_condition]
        load_tide = nc.load_tide_fes.values.ravel()[class_condition]
        pole_tide = nc.pole_tide.values.ravel()[class_condition]
        water_frac = nc.water_frac.values.ravel()[class_condition]
        phase_noise_std = nc.phase_noise_std.values.ravel()[class_condition]
        dheight_dphase = nc.dheight_dphase.values.ravel()[class_condition]
        sig0 = nc.sig0.values.ravel()[class_condition]

        # correction for solid earth/load/pole tide effects (e.g., see SWOT User Handbook, section 3.1.25)
        heightEGM = height - geoid - solid_earth_tide - load_tide - pole_tide

        # create geodataframe
        data = {
            "height": height,
            "heightEGM": heightEGM,
            "lat": lat_flat,
            "lon": lon_flat,
            "geoid": geoid,
            "solid_earth_tide":solid_earth_tide,
            "load_tide":load_tide,
            "pole_tide":pole_tide,
            "class": class_flat,
            "water_frac": water_frac,
            "phase_noise_std": phase_noise_std,
            "dheight_dphase": dheight_dphase,
            "sig0": sig0,
        }
        gdf = gpd.GeoDataFrame(
            pd.DataFrame(data), geometry=gpd.points_from_xy(lon_flat, lat_flat)
        )
        gdf.set_crs(epsg=4326, inplace=True)

        ## Trim data to buffer around imported centerline
        if aoi is not None:
            gdf = gpd.clip(gdf, aoi)

    return gdf

def download_granule_list(granule_list, download_path, aoi: gpd.GeoDataFrame = None, classes=['open_water'], redownload=False):
    for granule in granule_list:

        # # check if already downloaded
        filename = str(granule.data_links).split("['https://archive.swot.podaac.earthdata.nasa.gov/podaac-swot-ops-cumulus-protected/SWOT_L2_HR_PIXC_D/")[1].split("']")[0]
        
        # check if trimmed data exists
        savepath = os.path.join(download_path, filename.replace(".nc", "_trimmed.geojson"))
        if os.path.exists(savepath) and redownload==False:
            print(f"Trimmed file {savepath} already exists, skipping download and processing.")
            continue

        filepath = os.path.join(download_path, filename)
        if not os.path.exists(filepath):
            earthaccess.download(granule, download_path)


        # Once downloaded, process to AOI and save trimmed data
        gdf_pixc = readPIXC(filepath, aoi=aoi, classes=classes)

        # save to geojson
        gdf_pixc.to_file(savepath)

        # close file and remove to save space
        os.remove(filepath)