import calendar
import os.path
from datetime import datetime
from typing import List, Dict, Optional

import numpy as np
from geopandas import GeoDataFrame
from rasterio.enums import Resampling
from rasterio.warp import reproject

from digitalarztools.adapters.data_manager import DataManager
from digitalarztools.io.file_io import FileIO
from digitalarztools.io.raster.band_process import BandProcess
from digitalarztools.io.raster.rio_process import RioProcess
from digitalarztools.io.raster.rio_raster import RioRaster
from digitalarztools.io.vector.gpd_vector import GPDVector


class RioRasterCollection:
    def __init__(self, raster_fps: list, output_path: Optional[str]=None):
        self.output_path = output_path
        self.raster_fps = raster_fps

    @staticmethod
    def get_rasters_fp(imagery_folder: str) -> List[str]:
        return FileIO.list_files_in_folder(imagery_folder, ext="tif")

    def add_raster_fp(self, file_path: str, meta_data):
        self.raster_fps.append(file_path)
        meta_data = self.add_timestamp_from_month_year(meta_data)
        self.meta_data.append(meta_data)

    @staticmethod
    def add_timestamp_from_month_year(meta: dict) -> dict:
        """
        Adds 'timestamp' key to meta dict if 'month' and 'year' exist.
        Sets timestamp to the first day of that month at 00:00:00.
        """
        if "month" in meta and "year" in meta:
            try:
                meta["timestamp"] = datetime(
                    year=int(meta["year"]),
                    month=int(meta["month"]),
                    day=1
                )
            except ValueError as e:
                print(f"[WARNING] Invalid date in metadata: {e}")
        else:
            print("[INFO] Skipping timestamp creation: 'month' or 'year' missing")
        return meta

    def calculates_stats(self, base_folder, base_name: str, aoi_gdf: GeoDataFrame = None,
                         purpose: str = None) -> DataManager:
        dm_base_folder = os.path.join(base_folder, "raster_stats")
        data_manager = DataManager(dm_base_folder, base_name, purpose)
        union_gdf = GPDVector.get_unary_union_gdf(aoi_gdf)
        geom = union_gdf.geometry.values[0]
        for fp in self.raster_fps:
            raster = RioRaster(fp)
            raster.clip_raster(union_gdf)
            for i in range(raster.get_spectral_resolution()):
                stats = BandProcess.get_summary_data(raster.get_data_array(i + 1))
                stats["file_path"] = os.path.relpath(fp, self.imagery_folder)
                stats["file_name"] = os.path.basename(fp)
                fn, ext = FileIO.get_file_name_ext(fp)
                data_manager.add_record(fn, stats, geom=geom.wkb)
        return data_manager

    def get_stats_data_manager(self, base_dir: str, base_name: str):
        dm_base_folder = os.path.join(base_dir, "raster_stats")
        return DataManager(dm_base_folder, base_name)

    def get_max_raster(self) -> Optional[RioRaster]:
        if not self.raster_fps:
            return None
        rasters = [RioRaster(fp) for fp in self.raster_fps]
        max_data = rasters[0].get_data_array()
        for raster in rasters[1:]:
            max_data = np.maximum(max_data, raster.get_data_array())
        return rasters[0].rio_raster_from_array(max_data)

    def get_min_raster(self) -> Optional[RioRaster]:
        if not self.raster_fps:
            return None
        rasters = [RioRaster(fp) for fp in self.raster_fps]
        min_data = rasters[0].get_data_array()
        for raster in rasters[1:]:
            min_data = np.minimum(min_data, raster.get_data_array())
        return rasters[0].rio_raster_from_array(min_data)

    @staticmethod
    def match_raster_to(reference_raster, target_raster):
        data = target_raster.read(
            out_shape=reference_raster.shape,
            resampling=Resampling.nearest
        )
        return data
    @staticmethod
    def reproject_to_match(raster: RioRaster, reference_raster: RioRaster) -> np.ndarray:
        # Prepare output array with shape and dtype of reference
        out_shape = reference_raster.get_img_resolution()
        num_bands = raster.get_spectral_resolution()
        dst_array = np.zeros((num_bands, *out_shape), dtype=raster.get_dtype())

        for band_idx in range(num_bands):
            reproject(
                source=raster.get_data_array(),
                destination=dst_array[band_idx],
                src_transform=raster.get_geo_transform(),
                src_crs=raster.get_crs(),
                dst_transform=reference_raster.get_geo_transform(),
                dst_crs=reference_raster.get_crs(),
                resampling=Resampling.nearest
            )

        return dst_array

    def get_sum_raster(self, ignore_value: List[float] = ()) -> Optional[RioRaster]:
        if not self.raster_fps:
            return None

        rasters = [RioRaster(fp) for fp in self.raster_fps]
        reference_raster = rasters[0]
        sum_data = reference_raster.get_data_array().astype(float)
        valid_mask = ~np.isin(sum_data, ignore_value)
        sum_data = np.where(valid_mask, sum_data, 0.0)
        # count_data = valid_mask.astype(float)

        # Process remaining rasters
        for raster in rasters[1:]:
            data = self.reproject_to_match(raster, reference_raster).astype(float)
            mask = ~np.isin(data, ignore_value)
            sum_data += np.where(mask, data, 0.0)
            # count_data += mask.astype(float)

        # Avoid division by zero
        # with np.errstate(divide='ignore', invalid='ignore'):
        #     mean_data = np.true_divide(sum_data, count_data)
            # mean_data[count_data == 0] = np.nan  # Or any other fill value if needed

        return reference_raster.rio_raster_from_array(sum_data)

    def get_mean_raster(self, ignore_value: List[float] = ()) -> Optional[RioRaster]:
        if not self.raster_fps:
            return None

        rasters = [RioRaster(fp) for fp in self.raster_fps]
        reference_raster = rasters[0]
        sum_data = reference_raster.get_data_array().astype(float)
        valid_mask = ~np.isin(sum_data, ignore_value)
        sum_data = np.where(valid_mask, sum_data, 0.0)
        count_data = valid_mask.astype(float)

        # Process remaining rasters
        for raster in rasters[1:]:
            data = self.reproject_to_match(raster, reference_raster).astype(float)
            mask = ~np.isin(data, ignore_value)
            sum_data += np.where(mask, data, 0.0)
            count_data += mask.astype(float)

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            mean_data = np.true_divide(sum_data, count_data)
            # mean_data[count_data == 0] = np.nan  # Or any other fill value if needed

        return reference_raster.rio_raster_from_array(mean_data)

    def get_latest_raster(self) -> Optional[RioRaster]:
        if not self.raster_fps or not self.meta_data:
            return None

        # Pair file paths with timestamps
        timestamped_rasters = []
        for fp, meta in zip(self.raster_fps, self.meta_data):
            ts = meta.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)  # Convert string to datetime
            if ts is not None:
                timestamped_rasters.append((ts, fp))

        if not timestamped_rasters:
            return None  # No timestamps available

        # Sort by timestamp descending and pick latest
        latest_fp = sorted(timestamped_rasters, key=lambda x: x[0], reverse=True)[0][1]
        return RioRaster(latest_fp)

    def get_monthly_extreme(self, is_peak_intensity: bool = False, ignore_values=()) -> Optional[Dict]:
        """
        Returns the year and month of the raster with the extreme value.

        :param is_peak_intensity: If True, compare pixel-level extrema (min/max); otherwise, use mean.
        :param ignore_values: Tuple of values to ignore during calculations (e.g., (0,))
        """
        if not self.raster_fps or not self.meta_data:
            return None

        global_max = -np.inf
        global_min = np.inf
        max_years = []
        min_years = []

        for i, fp in enumerate(self.raster_fps):
            raster = RioRaster(fp)
            data = raster.get_data_array().astype(float)
            year = self.meta_data[i].get("year")

            # Mask ignored values
            for val in ignore_values:
                data[data == val] = np.nan
            summary_data = RioProcess.get_raster_summary_data(raster, ignore_values)
            max_vals = []
            min_vals = []
            mean_vals = []
            for band in summary_data:
                max_vals = summary_data[band]["max"]
                mean_vals = summary_data[band]["mean"]
                min_vals = summary_data[band]["min"]
            # Compute based on mode
            if is_peak_intensity:
                local_max = np.max(max_vals)
                local_min = np.min(min_vals)
            else:
                local_max = np.max(mean_vals)
                local_min = np.min(mean_vals)

            # Update global max
            if local_max > global_max:
                global_max = float(local_max)
                max_years = [year]
            elif local_max == global_max:
                max_years.append(year)

            # Update global min
            if local_min < global_min:
                global_min = float(local_min)
                min_years = [year]
            elif local_min == global_min:
                min_years.append(year)

        return {
            "max_value": global_max,
            "max_years": max_years,
            "min_value": global_min,
            "min_years": min_years
        }

