from datetime import datetime, timedelta
from typing import Literal

import ee

from digitalarztools.pipelines.gee.core.image_collection import GEEImageCollection
from digitalarztools.pipelines.gee.core.region import GEERegion


class ERA5Data:
    """
      in GEE
    https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR

    """

    def __init__(self):
        self.gee_dataset_tag = "ECMWF/ERA5_LAND/DAILY_AGGR"
        self.gee_scale = 11132  # Corrected to 11 km resolution

    def get_gee_dataset_collection(self, region: GEERegion) -> ee.ImageCollection:
        return ee.ImageCollection(self.gee_dataset_tag).filterBounds(region.aoi)

    def get_latest_dates(self, region: GEERegion, delta_in_days=10, end_date: datetime = None) -> (str, str):
        # Calculate the date range for the latest 10 days or any delta applied
        ee_img_coll = self.get_gee_dataset_collection(region=region)

        if end_date is None:
            end_date = GEEImageCollection.get_collection_max_date(ee_img_coll)

        if end_date is None:
            end_date = datetime.utcnow().date()

        start_date = end_date - timedelta(days=delta_in_days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    def get_snow_depth_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        Returns an ee.Image of the latest snow depth (meters).
        band: snow_depth
        unit: m
        description Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).
        @param gee_region:
        @param delta_in_days:
        """
        start_date_str, end_date_str = self.get_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        snow_depth_dataset = dataset.select("snow_depth")

        return snow_depth_dataset

    def get_snow_metric_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
        snow_cover (faction) → fraction of snow cover from 0 to 1
        snow_depth (m) → ❄️ Total snow thickness on the ground.
        snow_depth_water_equivalent (m) → 💧 Amount of water stored in snow.
        snowfall_sum (m) → 🌨️ New snow accumulation over time.
        snowmelt_sum (m) → 🌊 How much snow has melted (directly related to runoff).
        description Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).
        @param gee_region:
        @param delta_in_days:
        """
        start_date_str, end_date_str = self.get_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        snow_metric_dataset = dataset.select(
            ["snow_cover", "snow_depth", "snow_depth_water_equivalent", "snowfall_sum", "snowmelt_sum"])

        return snow_metric_dataset

    def get_runoff_metric_collection(self, gee_region: GEERegion, delta_in_days=10,
                                     stats: Literal["sum", "min", "max"] = "sum") -> ee.ImageCollection:
        """
        https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
        """
        if stats == "min":
            return self.get_min_runoff_metric_collection(gee_region, delta_in_days)
        elif stats == "max":
            return self.get_max_runoff_metric_collection(gee_region, delta_in_days)
        else:
            return self.get_sum_runoff_metric_collection(gee_region, delta_in_days)

    def get_sum_runoff_metric_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
        total_precipitation_sum (m): Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. I
        total_evaporation_sum (m of water equivalent): Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapor in the air above.
        runoff_sum: (m) The sum of these two is simply called 'runoff'.
        # runoff_min: daily  minimum runoff
        # runoff_max: daily  maximum runoff
        """
        start_date_str, end_date_str = self.get_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        runoff_dataset = dataset.select(
            ["total_precipitation_sum", "total_evaporation_sum", "runoff_sum"])

        return runoff_dataset

    def get_min_runoff_metric_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
        total_precipitation_min (m): Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. I
        total_evaporation_min (m of water equivalent): Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapor in the air above.
        runoff_min: (m) daily  minimum runoff

        """
        start_date_str, end_date_str = self.get_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        runoff_dataset = dataset.select(
            ["total_precipitation_min", "total_evaporation_min", "runoff_min"])

        return runoff_dataset

    def get_max_runoff_metric_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
        total_precipitation_max (m): Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. I
        total_evaporation_max (m of water equivalent): Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapor in the air above.
        runoff_max: (m) daily  minimum runoff

        """
        start_date_str, end_date_str = self.get_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        runoff_dataset = dataset.select(
            ["total_precipitation_max", "total_evaporation_max", "runoff_max"])

        return runoff_dataset
