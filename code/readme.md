# Workflow

## Exporting S2 images from GEE
* Run gee_exports_S2.ipynb with selected date range and roi (shapefile must be first loaded as an asset in GEE) (env: classic)
* Download files saved to drive
* Run geotif2png.py (WSL mamba activate classic, python geotif2png.py)
* Flip through images to explore timeseries