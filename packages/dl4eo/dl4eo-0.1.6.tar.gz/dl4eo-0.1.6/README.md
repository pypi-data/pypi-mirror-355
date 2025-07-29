# RSDL Pipeline

A modular Python package to process large-scale remote sensing datasets (Sentinel-2, Sentinel-1, DEM) and generate deep learning-ready inputs.

## Installation

```bash
conda env create -f environment.yml
```

## Usage

```python
from rsdl_pipeline.pipeline import run_pipeline
from rsdl_pipeline.config import PipelineConfig

config = PipelineConfig(
    base_dir="/path/to/workdir",
    aoi_shapefile="/path/to/aoi.shp",
    feature_shapefile="/path/to/lakes.shp",
    date_range="2020-08-01/2020-08-30",
    cloud_cover=20,
    box_size_m=2560,
    n_jobs=8
)
run_pipeline(config)
```