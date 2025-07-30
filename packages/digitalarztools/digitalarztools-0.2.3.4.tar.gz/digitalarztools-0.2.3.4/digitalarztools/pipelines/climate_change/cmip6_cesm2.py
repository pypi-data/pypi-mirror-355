import boto3
import os
import io
from botocore import UNSIGNED
from botocore.config import Config
import xarray as xr
from tqdm import tqdm

from digitalarztools.adapters.data_manager import DataManager

"""
https://nex-gddp-cmip6.s3.us-west-2.amazonaws.com/index.html#NEX-GDDP-CMIP6/CESM2/
"""

# AWS S3 bucket and base prefix
BUCKET_NAME = "nex-gddp-cmip6"
BASE_PREFIX = "NEX-GDDP-CMIP6/CESM2/"

# Define output directory
# OUTPUT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "madinah_region_data")
OUTPUT_DIR = '/Users/atherashraf/Documents/data/NASA/ClimateChange/CMIP6'
# OUTPUT_DIR = "madinah_region_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Scenarios and time periods
SCENARIOS = ["ssp126", "ssp245", "ssp370", "ssp585"]  # "historical"

"""
# Variables Description Table

| Variable   | Description                                        | Unit        |
|------------|----------------------------------------------------|-------------|
| hurs       | Relative Humidity at Surface Level                | %           |
| huss       | Specific Humidity at Surface Level                | kg/kg       |
| pr         | Precipitation                                     | K-m/sec     |
| rlds       | Downward Longwave Radiation at Surface            | W/m²        |
| rsds       | Downward Shortwave Radiation at Surface           | W/m²        |
| sfcWind    | Surface Wind Speed                                | m/s         |
| tas        | Near-Surface Air Temperature                      | K (Kelvin)  |

"""
# VARIABLES = ["hurs", "huss", "pr", "rlds", "rsds", "sfcWind", "tas"]

VARIABLES = ["pr", "tas"]

# Define the bounding box for the Madinah region
"""
Madinah Region  Extent
37.0840000145728581,22.5197100612640675 : 42.1587300198428352,27.4733099473733766

"""
LAT_MIN = 22.5197100612640675
LAT_MAX = 27.4733099473733766
LON_MIN = 37.0840000145728581
LON_MAX = 42.1587300198428352

# Initialize S3 client
s3_client = boto3.client("s3", config=Config(signature_version=UNSIGNED))


def list_objects(bucket, prefix):
    """List objects in an S3 bucket with a given prefix."""
    objects = []
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    while response.get("KeyCount", 0) > 0:
        objects.extend(response.get("Contents", []))
        if response.get("IsTruncated"):
            response = s3_client.list_objects_v2(
                Bucket=bucket, Prefix=prefix, ContinuationToken=response["NextContinuationToken"]
            )
        else:
            break
    return objects


def process_and_crop_file(key, output_dir, need_crop=True):
    """Download a NetCDF file from S3, optionally crop to Madinah region, and save locally."""
    try:
        # print(f"Processing {key}...")
        output_file = os.path.join(output_dir, key.replace("/", "_"))

        if not os.path.exists(output_file):
            # Download the file into memory
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            file_content = response["Body"].read()  # Read file content into memory

            # Open the file as an xarray dataset
            with xr.open_dataset(io.BytesIO(file_content), engine="h5netcdf") as ds:
                # Crop if needed
                if need_crop:
                    ds = ds.sel(lat=slice(LAT_MIN, LAT_MAX), lon=slice(LON_MIN, LON_MAX))
                    # print(f"Cropped data to Madinah region.")

                # Save the dataset to disk
                ds.to_netcdf(output_file)
                # print(f"Data saved to {output_file}")
        return output_file

    except Exception as e:
        print(f"Error processing {key}: {e}")


if __name__ == "__main__":
    dm = DataManager(
        folder_path=OUTPUT_DIR,
        base_name='cc_cmip6_ssp_info',
        purpose="Data Manager for Climate Change SSP Scenarios using CMIP6 CESM2"
    )
    # Loop through scenarios
    for scenario in SCENARIOS:
        scenario_prefix = f"{BASE_PREFIX}{scenario}/"
        members = list_objects(BUCKET_NAME, scenario_prefix)
        member_folders = set(obj["Key"].split("/")[3] for obj in members if "/" in obj["Key"])

        # Loop through members (e.g., r4i1p1f1)
        for member in member_folders:
            member_prefix = f"{scenario_prefix}{member}/"
            print(f"Processing member: {member_prefix}...")
            # Loop through variables (e.g., hurs, pr, tas)
            for variable in VARIABLES:
                # print(f"Processing variable: {variable}...")
                variable_prefix = f"{member_prefix}{variable}/"
                files = list_objects(BUCKET_NAME, variable_prefix)
                var_output_dir = os.path.join(OUTPUT_DIR, variable)
                os.makedirs(var_output_dir, exist_ok=True)
                # Process .nc files
                for file in tqdm(files, desc=f"Processing variable: {variable} of {scenario_prefix} files", total=len(files)):
                    key = file["Key"]
                    if variable == 'pr' and '_v1.1' not in key:
                        continue

                    if key.endswith(".nc"):
                        output_file = process_and_crop_file(key,var_output_dir, need_crop=False)
                        # Split the file name into parts based on underscores
                        parts = os.path.basename(output_file).split("_")

                        # Construct a relative file path for storage
                        fp = os.path.relpath(str(output_file), str(OUTPUT_DIR))

                        # Create a record dictionary with metadata extracted from the file name
                        record = {
                            "file_path": fp,  # Relative file path
                            "dataset": parts[0],  # Dataset name, e.g., NEX-GDDP-CMIP6
                            "model": parts[1],  # Climate model, e.g., CESM2
                            "scenario": parts[2],  # Socioeconomic scenario, e.g., ssp126
                            "realization": parts[3],  # Realization details, e.g., r4i1p1f1
                            "variable": parts[4],  # Variable, e.g., pr (precipitation)
                            "time_scale": f"{parts[5]}_{parts[6]}",  # Time scale, e.g., pr_day
                            "grid_label": parts[10],  # Grid label, e.g., gn
                            "year": parts[11].replace(".nc", ""),  # Year of the data, e.g., 2053 (removing .nc)
                            "version": parts[12].replace(".nc", "") if len(parts) > 12 else "v1.0"
                            # Version, default to v1.0
                        }

                        # Generate a unique key for the record using variable, scenario, year, and version
                        key = f'{record["variable"]}_{record["scenario"]}_{record["year"]}_{record["version"]}'

                        # Add the record to the DataManager
                        is_added = dm.add_record(key, record)

    print("Processing complete.")
