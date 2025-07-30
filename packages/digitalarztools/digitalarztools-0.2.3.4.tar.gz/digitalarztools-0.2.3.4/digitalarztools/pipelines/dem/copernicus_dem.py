import boto3
import os
from botocore import UNSIGNED
from botocore.config import Config
from tqdm import tqdm

def download_copernicus_dem(region_coords, resolution='30m', output_dir='./madinah_dem'):
    """
    Download Copernicus DEM and auxiliary files for a specified region using AWS Open Data.

    Parameters:
        region_coords (list): List of bounding box coordinates [min_lon, min_lat, max_lon, max_lat].
        resolution (str): Resolution of the DEM ('30m' or '90m').
        output_dir (str): Directory to save the downloaded files.
    """
    bucket_name = 'copernicus-dem-30m' if resolution == '30m' else 'copernicus-dem-90m'
    prefix = 'Copernicus_DSM_COG_10_'

    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    non_dem_output_dir = os.path.join(output_dir, "non_dem")
    os.makedirs(non_dem_output_dir, exist_ok=True)

    # Initialize the S3 client with unsigned access
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED), region_name='us-west-2')

    print("Fetching files from AWS S3 bucket...")
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    # File extensions to identify auxiliary files
    auxiliary_extensions = ['_ACM.kml', '_EDM.tif', '_HEM.tif', '_FLM.tif']

    for page in pages:
        if 'Contents' not in page:
            continue

        for obj in tqdm(page['Contents'], desc="Downloading Tiles"):
            key = obj['Key']

            # Check if the file matches DEM or auxiliary criteria
            is_auxiliary_file = any(key.endswith(ext) for ext in auxiliary_extensions)
            is_dem_file = key.endswith('_DEM.tif')

            if not (is_dem_file or is_auxiliary_file):
                # Skip unrelated files
                continue

            try:
                # Extract longitude and latitude info
                lon_lat_info = key.split('_')[-3:-1]
                tile_lon = int(lon_lat_info[0].replace('W', '-').replace('E', ''))
                tile_lat = int(lon_lat_info[1].replace('S', '-').replace('N', ''))
            except (ValueError, IndexError):
                # Skip files with invalid naming patterns
                print(f"Skipping invalid file: {key}")
                continue

            # Check if the tile falls within the bounding box
            min_lon, min_lat, max_lon, max_lat = region_coords
            if not (min_lon <= tile_lon <= max_lon and min_lat <= tile_lat <= max_lat):
                continue

            # Determine the output folder
            if is_dem_file:
                file_name = os.path.join(output_dir, os.path.basename(key))
            else:
                file_name = os.path.join(non_dem_output_dir, os.path.basename(key))

            # Download the file if it doesn't already exist
            if not os.path.exists(file_name):
                print(f"Downloading {file_name}...")
                s3.download_file(bucket_name, key, file_name)

    print(f"DEM and auxiliary files downloaded to {output_dir} and {non_dem_output_dir}")


if __name__ == "__main__":
    # Define the bounding box for Madinah region in EPSG:4326 (lat/lon)
    madinah_bbox = [37.074437910243304, 22.512577028172675, 42.1950402673047, 27.496387330433468]
    download_copernicus_dem(madinah_bbox, resolution='30m')
