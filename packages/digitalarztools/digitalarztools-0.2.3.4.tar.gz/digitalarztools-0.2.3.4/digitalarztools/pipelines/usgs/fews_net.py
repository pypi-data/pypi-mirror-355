import enum
from datetime import datetime, timedelta

import ee

from digitalarztools.pipelines.gee.core.image_collection import GEEImageCollection
from digitalarztools.pipelines.gee.core.region import GEERegion


class FEWSNetData:
    """
    https://earlywarning.usgs.gov/fews/datadownloads/Global/CHIRPS%202.0
    in GEE
    https://developers.google.com/earth-engine/datasets/catalog/NASA_FLDAS_NOAH01_C_GL_M_V001
    """

    def __init__(self):
        self.gee_dataset_tag = "NASA/FLDAS/NOAH01/C/GL/M/V001"
        self.gee_scale = 11132  # ✅ Corrected to 11 km resolution

    def get_gee_dataset_collection(self, region: GEERegion) -> ee.ImageCollection:
        return ee.ImageCollection(self.gee_dataset_tag).filterBounds(region.bounds)

    def get_latest_dates(self, region: GEERegion, delta_in_days=10) -> (str, str):
        # Calculate the date range for the latest 10 days
        ee_img_coll = self.get_gee_dataset_collection(region=region)
        end_date = GEEImageCollection.get_collection_max_date(ee_img_coll)

        # ✅ Fix: Handle missing dates gracefully
        if not end_date:
            end_date = datetime.utcnow().date()

        start_date = end_date - timedelta(days=delta_in_days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    def get_snow_depth_collection(self, gee_region: GEERegion, delta_in_days=7) -> ee.ImageCollection:
        """
        Returns an ee.Image of the latest snow depth (meters).
        """
        start_date_str, end_date_str = self.get_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        snow_depth_dataset = dataset.select("SnowDepth_inst")

        return snow_depth_dataset

    def get_snow_volume(self, gee_region: GEERegion, delta_in_days=7) -> dict:
        """
        Computes total snow volume (m³) over the given AOI.
        """
        snow_depth_img = self.get_snow_depth_collection(gee_region, delta_in_days)

        # ✅ Compute Pixel Area (m²)
        pixel_area = ee.Image.pixelArea()

        # ✅ Compute Snow Volume (m³)
        snow_volume_img = snow_depth_img.multiply(pixel_area)

        # ✅ Reduce to a single value
        total_snow_volume = snow_volume_img.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=gee_region.bounds,
            scale=self.gee_scale,  # ✅ Corrected scale to 11km
            maxPixels=1e9
        ).get("SnowDepth_inst")

        # ✅ Compute Total AOI Area (m²)
        total_area = pixel_area.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=gee_region.bounds,
            scale=self.gee_scale,
            maxPixels=1e9
        ).get("area")

        # ✅ Convert to Python values
        snow_volume = total_snow_volume.getInfo() if total_snow_volume else 0
        area = total_area.getInfo() if total_area else 1  # Avoid division by zero
        avg_snow_depth = snow_volume / area if area > 0 else 0

        # ✅ Compute Surface Runoff (30% of Snow Volume)
        runoff_volume = snow_volume * 0.3

        return {
            "Snow Volume (m³)": snow_volume,
            "Surface Runoff (m³)": runoff_volume,
            "Average Snow Depth (m)": avg_snow_depth
        }
