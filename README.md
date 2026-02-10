# EO analysis of Usangu wetlands

Code and notebooks for eo analysis of the hydrology of the Usangu wetlands in Tanzania. Current repo functions include:

**SWOT:**
* Downloading SWOT pixel cloud data
* Processing SWOT pixel cloud data to 100 m raster format
* Creating weekly or monthly aggregates of pixel cloud rasters
* Creating occurance product from pixel cloud raster

**Sentinel-2:**
* Batch downloading S2 optical imagery in selected AOIs

**PALSAR-2:**
* Comparison of PALSAR2 backscatter in a flooded forest with rainfall runoff model output and nearest in situ river gauge.

Interesting questions/investigations:
* How do spatial patterns in SWOT flooded areas relate to methane emissions patterns as observed by Sentinel-5?
* Do large scale burn events in the dry season have an effect on Sentinel-5 emissions observations?
* Seasonal and interannual variability: Is the hydrology of Usangu changing? Visisble from SWOT? Other radar satellites? GRACE? 
* Are there any distict spatial patterns observable with EO?

Known issues:
* 'Shadow rivers' in SWOT pixel cloud raster - caused by geolocation errors
* Data loss in low coherence zones (near NADIR)
* Underestimation of flood extent underneath vegetation, most prominant in the permanant swamp (central part of Eastern Usangu wetlands). Unknown how much this region is actually flooded. 


## Getting Started

To get started wih this repo on yout local computer, type this in your terminal:

```sh
git clone https://github.com/selfr-eo/eo_analysis_usangu.git
cd eo_analysis_usangu
```
Or open up the folder with GitHub Desktop.

There are 2 separate environments (one conda, one uv) used within this repository, for different functions, due to dependency clashes. For most activities, you will use the conda environment. However, if you wish to download SWOT data, the uv environment should be utilized. Follow the steps below for setting up each on your local computer.

### Conda environment
To install packages for running pixel cloud processing scripts copy the following into your terminal:

```sh
mamba env create -f environment.yml
mamba activate hydroeo
```

### uv environment
To install packages needed to **download** pixel cloud data with uv: (NOTE: this is a separate environment than the previous, due to dependency clashes with geospatial packages)

```sh
uv venv
uv sync
```
Then to activate the environment:

Windows (PowerShell)
```sh
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```sh
source .venv/bin/activate
```