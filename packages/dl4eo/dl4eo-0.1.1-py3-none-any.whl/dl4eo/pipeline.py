import os
import subprocess
from .config import PipelineConfig

def generate_dataset(base_dir, aoi_shapefile, feature_shapefile, date_range,
                     cloud_cover=20, box_size_m=2560, n_jobs=8):
    cfg = PipelineConfig(
        base_dir=base_dir,
        aoi_shapefile=aoi_shapefile,
        feature_shapefile=feature_shapefile,
        date_range=date_range,
        cloud_cover=cloud_cover,
        box_size_m=box_size_m,
        n_jobs=n_jobs
    )

    os.environ["RSDL_BASE_DIR"] = base_dir  # Optional: pass configs if needed to scripts
    os.environ["RSDL_DATE_RANGE"] = date_range
    os.environ["RSDL_CLOUD_COVER"] = str(cloud_cover)
    os.environ["RSDL_BOX_SIZE"] = str(box_size_m)

    stages = [
        "download_sentinel2.py",
        "preprocess_s2.py",
        "generate_aoi.py",
        "prepare_dem.py",
        "prepare_sentinel1.py",
        "generate_mask.py",
        "normalize_data.py"
    ]

    stage_dir = os.path.join(os.path.dirname(__file__), "stages")
    for stage in stages:
        print(f"\n{'='*30} STAGE: {stage} {'='*30}\n")
        subprocess.run(["python", stage], cwd=stage_dir, check=True)