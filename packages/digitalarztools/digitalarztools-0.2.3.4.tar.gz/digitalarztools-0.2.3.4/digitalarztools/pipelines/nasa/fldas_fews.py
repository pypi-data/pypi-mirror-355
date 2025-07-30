from datetime import datetime, timedelta

import ee

from digitalarztools.pipelines.gee.core.image_collection import GEEImageCollection
from digitalarztools.pipelines.gee.core.region import GEERegion


class FLDASFews:
    """
      in GEE
        https://developers.google.com/earth-engine/datasets/catalog/NASA_FLDAS_NOAH01_C_GL_M_V001#bands
    """
    def __init__(self):
        self.gee_dataset_tag = "NASA/FLDAS/NOAH01/C/GL/M/V001"
        self.gee_scale = 11132  # Corrected to 11 km resolution

    def get_gee_dataset_collection(self, region: GEERegion) -> ee.ImageCollection:
        return ee.ImageCollection(self.gee_dataset_tag).filterBounds(region.aoi)

    def get_gee_latest_dates(self, region: GEERegion, delta_in_days=10, end_date: datetime = None) -> (str, str):
        # Calculate the date range for the latest 10 days or any delta applied
        ee_img_coll = self.get_gee_dataset_collection(region=region)

        if end_date is None:
            end_date = GEEImageCollection.get_collection_max_date(ee_img_coll)

        if end_date is None:
            end_date = datetime.utcnow().date()

        start_date = end_date - timedelta(days=delta_in_days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    def get_gee_snow_depth_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        Returns an ee.Image of the latest snow depth (meters).
        band: SnowDepth_inst
        unit: m
        description Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).
        @param gee_region:
        @param delta_in_days:
        """
        start_date_str, end_date_str = self.get_gee_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        snow_depth_dataset = dataset.select("SnowDepth_inst")

        return snow_depth_dataset

    def get_gee_snow_metric_collection(self, gee_region: GEERegion, delta_in_days=10) -> ee.ImageCollection:
        """
        https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
        SnowCover_inst (faction) → fraction of snow cover from 0 to 1
        SnowDepth_inst (m) → ❄️ snow depth on the ground.
        SWE_inst (kg/m^2) → 💧 Amount of water stored in snow.
        Snowf_tavg (kg/m^2/s) → 🌨️ snowfall rate.
        @param gee_region:
        @param delta_in_days:
        """
        start_date_str, end_date_str = self.get_gee_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(ee.Filter.date(start_date_str, end_date_str))
        snow_metric_dataset = dataset.select(["SnowCover_inst", "SnowDepth_inst", "SWE_inst", "Snowf_tavg"])

        return snow_metric_dataset

    def get_gee_runoff_metric_collection(
            self, gee_region: GEERegion, delta_in_days=10, in_mm: bool = True
    ) -> ee.ImageCollection:
        """
        Fetch FLDAS runoff metric ImageCollection.

        If in_mm=True, converts all bands (precipitation, evaporation, total runoff)
        from kg/m^2/s to mm/day (1 kg/m²/s = 1 mm/s; mm/day = value * 86400)

        Bands:
            - Rainf_f_tavg  (kg/m^2/s): Total precipitation rate
            - Evap_tavg     (kg/m^2/s): Evapotranspiration
            - Qs_tavg       (kg/m^2/s): Storm surface runoff
            - Qsb_tavg      (kg/m^2/s): Baseflow-groundwater runoff
        Returns:
            ImageCollection with bands: total_precipitation, total_evaporation, total_runoff
        """
        start_date_str, end_date_str = self.get_gee_latest_dates(gee_region, delta_in_days)
        dataset = self.get_gee_dataset_collection(gee_region).filter(
            ee.Filter.date(start_date_str, end_date_str)
        )

        def compute_runoff_and_convert(img):
            runoff = img.select("Qs_tavg").add(img.select("Qsb_tavg")).rename("total_runoff")
            precip = img.select("Rainf_f_tavg").rename("total_precipitation")
            evap = img.select("Evap_tavg").rename("total_evaporation")

            combined = runoff.addBands([precip, evap])

            if in_mm:
                seconds_per_day = ee.Number(86400)
                combined = combined.multiply(seconds_per_day).copyProperties(img, img.propertyNames())

            return combined.set("system:time_start", img.get("system:time_start"))

        return dataset.map(compute_runoff_and_convert)
