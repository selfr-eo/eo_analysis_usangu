
import geopandas as gpd
import os
import datetime
import pandas as pd
import shapely
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from scipy.stats import binned_statistic_2d
from rasterio.transform import from_origin



def load_trimmed_pixc_data(trimmed_filelist):
    gdf_pixc_all = gpd.GeoDataFrame()
    for trimmed_file in trimmed_filelist:
        # check file size - skip if 0 bytes
        if os.path.getsize(trimmed_file) < 10000:  # less than 10 KB
            print(f"Skipping empty file: {trimmed_file}")
            continue

        str_date = os.path.basename(trimmed_file).split("_")[-4]
        # parse yyyymmddThhmmss to datetime
        t = datetime.datetime.strptime(str_date, "%Y%m%dT%H%M%S")
        gdf_temp = gpd.read_file(trimmed_file)
        gdf_temp['date'] = t
        # set index to date
        gdf_temp = gdf_temp.set_index('date')
        gdf_pixc_all = pd.concat([gdf_pixc_all, gdf_temp])
    
    return gdf_pixc_all

def grid_from_shp(shapefile_utm: gpd.GeoDataFrame, grid_size: float, buffer: float = 0.0, plotFlag=False) -> gpd.GeoDataFrame:

    # shapefile: input shapefile to cover with grid in UTM coordinates
    # grid_size: size of grid cells in meters
    # buffer: buffer around shapefile extent in meters


    # Create a grid covering the shapefile extent
    bounds = shapefile_utm.total_bounds  # (minx, miny, maxx, maxy)
    grid_box = shapely.geometry.box(shapefile_utm.total_bounds[0], shapefile_utm.total_bounds[1], shapefile_utm.total_bounds[2], shapefile_utm.total_bounds[3]).buffer(buffer)  # small buffer to ensure coverage

    pixel_half_size = grid_size / 2
    x_coords = np.arange(grid_box.bounds[0] + pixel_half_size, grid_box.bounds[2]-pixel_half_size, grid_size)
    y_coords = np.arange(grid_box.bounds[1] + pixel_half_size, grid_box.bounds[3]-pixel_half_size, grid_size)
    X, Y = np.meshgrid(x_coords, y_coords)
    x_coords_flat = X.flatten()
    y_coords_flat = Y.flatten()

    if plotFlag:
        fig, ax = plt.subplots(figsize=(10, 10))
        shapefile_utm.plot(ax=ax)
        grid_box_gdf = gpd.GeoDataFrame(geometry=[grid_box], crs=shapefile_utm.crs)
        grid_box_gdf.plot(ax=ax, facecolor="none", edgecolor="red")
        plt.scatter(X, Y, color='blue', s=0.1)
        plt.show()

    return x_coords_flat, y_coords_flat


def plot_hist_map(gdf_date, field, shapefile_ll, date, outdir):

    fig, (ax_hist, ax_map) = plt.subplots(
        ncols=2,
        figsize=(16, 8),
        gridspec_kw={"width_ratios": [1, 1]}
    )

    ax_hist.hist(
                gdf_date[field],
                bins=100,
                alpha=0.4,
                density=True,
                label=str(date)
            )

    ax_hist.set_xlabel(f"{field}")
    ax_hist.set_ylabel("Probability density")

    # Background
    shapefile_ll.plot(ax=ax_map, color="lightgrey", edgecolor="none")

    # min and max set as 3 std away from mean
    vmin = gdf_date[field].mean() - 3 * gdf_date[field].std()
    vmax = gdf_date[field].mean() + 2 * gdf_date[field].std()

    # Points colored by height
    gdf_date.plot(
        ax=ax_map,
        column=field,
        legend=True,
        markersize=0.5,
        vmin=vmin,
        vmax=vmax
    )

    ax_map.set_title(str(date))
    ax_map.set_axis_off()

    # save figure
    fig.savefig(outdir + f"{date}.png", dpi=300)

    # close figure
    plt.close(fig)


def grid_sampling(shapefile_utm: gpd.GeoDataFrame, 
                  gdf_points: gpd.GeoDataFrame, 
                  buffer: float = 0.0, 
                  field: str = 'heightEGM', 
                  stat_method: str = 'median', 
                  grid_resolution: float = 100, 
                  filedate: str = ' ', 
                  plotFlag=False, 
                  countFlag=False,
                  writeGeoTIFF=False,
                  swot_raster_dir: str = "./") -> np.ndarray:
    
    # Function that grids point data to specified resolution over shapefile extent
    # shapefile_utm: input shapefile to cover with grid in UTM coordinates
    # gdf_points: input geopandas dataframe with point data to grid
    # buffer: buffer around shapefile extent in meters
    # field: field in gdf_points to grid
    # stat_method: statistic to compute in each grid cell ('median', 'mean', etc.)
    # grid_resolution: size of grid cells in meters
    # filedate: string to append to output filename - e.g., date or 'all_dates'
    # plotFlag: whether to plot the gridded result
    # writeGeoTIFF: whether to write the gridded result to GeoTIFF
    # swot_raster_dir: directory to save GeoTIFF if writeGeoTIFF is True


    x_grid, y_grid = grid_from_shp(shapefile_utm, grid_size=grid_resolution, buffer=buffer, plotFlag=plotFlag)

    # convert gdf_pixc_all to UTM
    gdf_points = gdf_points.to_crs(shapefile_utm.crs)

    # Extract swot pixc arrays
    x = gdf_points.geometry.x.to_numpy()
    y = gdf_points.geometry.y.to_numpy()
    z = gdf_points[field].to_numpy()

    # Grid resolution
    dx = dy = grid_resolution

    # Grid extent (match your defined grid)
    xmin = x_grid.min()
    xmax = x_grid.max()
    ymin = y_grid.min()
    ymax = y_grid.max()

    # Number of cells
    nx = int(np.ceil((xmax - xmin) / dx))
    ny = int(np.ceil((ymax - ymin) / dy))

    # Pure scipy method (fast)
    x_edges = xmin + dx * np.arange(nx + 1)
    y_edges = ymin + dy * np.arange(ny + 1)

    # create 2D binned statistic for median
    stat_raster, _, _, _ = binned_statistic_2d(
        y, x, z,
        statistic=stat_method,
        bins=[y_edges, x_edges]
    )

    count_raster, _, _, _ = binned_statistic_2d(
        y, x, None,
        statistic="count",
        bins=[y_edges, x_edges]
    )

    stat_raster = np.flipud(stat_raster)
    count_raster = np.flipud(count_raster)

    transform = from_origin(
        xmin,
        ymax,
        dx,
        dy
    )

    if plotFlag:
        # Plot results
        fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 6))
        c1 = ax1.imshow(stat_raster, cmap="viridis", extent=(xmin, xmax, ymin, ymax))
        ax1.set_title(f"{stat_method.capitalize()} {field}")
        c2 = ax2.imshow(count_raster, cmap="viridis", extent=(xmin, xmax, ymin, ymax))
        ax2.set_title("Count of Points")

    # Write to geotiff
    if writeGeoTIFF:
        with rasterio.open(
            swot_raster_dir+f"{filedate}_{field}.tif",
            "w",
            driver="GTiff",
            height=stat_raster.shape[0],
            width=stat_raster.shape[1],
            count=1,
            dtype=stat_raster.dtype,
            crs=shapefile_utm.crs,
            transform=transform,
            nodata=np.nan
        ) as dst:
            dst.write(stat_raster, 1)

        if countFlag:
            with rasterio.open(
                swot_raster_dir+f"{filedate}_count.tif",
                "w",
                driver="GTiff",
                height=count_raster.shape[0],
                width=count_raster.shape[1],
                count=1,
                dtype=count_raster.dtype,
                crs=shapefile_utm.crs,
                transform=transform,
                nodata=np.nan
            ) as dst:
                dst.write(count_raster, 1)

    return stat_raster