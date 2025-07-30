import json
import os
import time

import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

from settings import DATA_DIR


class GraceDatasetsPipeline:
    """
    Groundwater and Soil Moisture Conditions from GRACE and GRACE-FO Data Assimilation L4 7-days 0.25 x 0.25 degree Global V3.0
    Data available at:
        https://disc.gsfc.nasa.gov/datasets/GRACEDADM_CLSM025GL_7D_3.0/summary?keywords=grace%20data
    Available via both direct links and S3.

    NASA EarthData Login is required for downloading files.
    """

    def __init__(self, urls_file, download_dir="grace_data"):
        with open(urls_file, 'r') as f:
            self.urls = f.read().splitlines()

        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

        # Get NASA credentials from environment variables
        self.username = os.environ.get('NASA_USERNAME')
        self.password = os.environ.get('NASA_PASSWORD')

        if not self.username or not self.password:
            raise ValueError("❌ NASA_USERNAME and NASA_PASSWORD must be set as environment variables.")

        # Create a persistent session with authentication
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

        # Ensure session properly stores cookies
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})  # Mimic a browser

        # Check authentication before downloading
        self.check_authentication()

    def check_authentication(self):
        """Check if NASA authentication is working before downloading files."""
        test_url = self.urls[0]  # Pick the first URL for authentication test

        print("🔄 Checking NASA Earthdata authentication...")
        response = self.session.get(test_url, allow_redirects=True)

        if response.status_code == 401:
            raise ValueError("❌ Authentication failed! Check NASA_USERNAME and NASA_PASSWORD.")
        elif response.status_code in [302, 303]:
            print(f"✅ Authentication successful! Redirected to signed URL.")
        elif response.status_code == 200:
            print(f"✅ Authentication successful! Direct access confirmed.")
        else:
            print(f"⚠️ Unexpected authentication response: {response.status_code}")

    def get_signed_url(self, url):
        """Get the actual signed download URL by handling NASA Earthdata redirects properly."""
        try:
            # print(f"🔄 Requesting signed URL for: {url}")
            response = self.session.get(url, allow_redirects=False)

            if response.status_code in [302, 303]:  # Redirect response
                signed_url = response.headers.get("Location")
                if signed_url:
                    # print(f"✅ Got signed URL: {signed_url}")
                    return signed_url
                else:
                    raise ValueError("❌ Failed to extract signed URL from headers.")
            else:
                raise ValueError(f"❌ Unexpected response code: {response.status_code} for {url}")

        except requests.exceptions.RequestException as e:
            raise ValueError(f"❌ Failed to get signed URL for {url}: {e}")

    def download_files(self):
        for url in tqdm(self.urls, desc="Downloading GRACE Data", total=len(self.urls)):
            file_name = os.path.basename(url)
            local_file_path = os.path.join(self.download_dir, file_name)

            # Skip if file already exists
            if os.path.exists(local_file_path):
                print(f"✅ {file_name} already exists, skipping.")
                continue

            try:
                # print(f"📥 Getting signed URL for {file_name}...")
                signed_url = self.get_signed_url(url)

                # print(f"📥 Downloading {file_name} from signed URL...")

                retry_attempts = 3  # Number of retries for network failures
                for attempt in range(retry_attempts):
                    try:
                        with self.session.get(signed_url, stream=True, allow_redirects=True) as response:
                            response.raise_for_status()

                            with open(local_file_path, 'wb') as file:
                                for chunk in response.iter_content(chunk_size=8192):
                                    file.write(chunk)

                        # print(f"✅ Saved: {local_file_path}")
                        break  # Exit retry loop if successful

                    except requests.exceptions.RequestException as e:
                        print(f"⚠️ Attempt {attempt + 1} failed. Retrying in 5 seconds...")
                        time.sleep(5)

                else:
                    print(f"❌ Failed to download {file_name} after {retry_attempts} attempts.")

            except Exception as e:
                  print(f"❌ Failed to download {file_name}: {e}")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config')
    # credentials_path = os.path.join(config_path, 'nasa_garce_data_credentiels.json')
    # s3_urls_file = os.path.join(config_path, 'subset_GRACEDADM_CLSM025GL_7D_3.0_20250302_094441_S3URLs.txt')
    urls_file = os.path.join(config_path, 'subset_GRACEDADM_CLSM025GL_7D_3.0_20250302_092705_.txt')
    download_dir = DATA_DIR
    pipeline = GraceDatasetsPipeline(urls_file, download_dir)
    # pipeline.test_bucket()
    pipeline.download_files()

# # Define the dataset URL and directory for saving files
# data_url = "https://disc.gsfc.nasa.gov/datasets/GRACEDADM_CLSM025GL_7D_3.0/summary?keywords=grace%20data"
# # data_url = "https://hydro1.gesdisc.eosdis.nasa.gov/data/GRACE_MONTHLY_L3/GFZ/GRACE_RL06_Mascon_CRI/"
# save_directory = "./grace_data/"
#
# # Create the directory if it does not exist
# os.makedirs(save_directory, exist_ok=True)
#
#
# # Function to download GRACE groundwater data for a given year and month
# def download_grace_data(year, month):
#     month_str = f"{month:02d}"  # Ensure month is two digits
#     file_name = f"GRCTellus.JPL.200204_202012.GLO.RL06M.MSCNv02CRIv02.nc"  # Example filename format
#
#     # Construct the URL for the specific file (check specific URLs on EarthData)
#     file_url = f"{data_url}/{year}/{file_name}"
#     file_path = os.path.join(save_directory, file_name)
#
#     # Download the file with authentication
#     response = requests.get(file_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
#
#     # Check if the request was successful
#     if response.status_code == 200:
#         with open(file_path, "wb") as f:
#             f.write(response.content)
#         print(f"Downloaded {file_name}")
#     else:
#         print(f"Failed to download {file_name}. Status code: {response.status_code}")
#
#
# # Download data for a range of years and months
# for year in range(2002, 2021):  # Example range; adjust as needed
#     for month in range(1, 13):
#         download_grace_data(year, month)
