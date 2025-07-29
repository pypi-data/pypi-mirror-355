from setuptools import setup, find_packages

setup(
    name="dl4eo",
    version="0.1.1",
    description="Deep Learning for Earth Observation - Data Preparation Pipeline",
    author="Saurabh Kaushik",
    author_email="saurabh21.kaushik@gmail.com",
    url="https://github.com/Sk-2103",
    packages=find_packages(include=["dl4eo", "dl4eo.*"]),
    install_requires=[
        "numpy", "rasterio", "geopandas", "shapely", "matplotlib",
        "joblib", "pystac-client", "fiona", "requests"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "dl4eo-run=dl4eo.pipeline:generate_dataset"
        ]
    }
)