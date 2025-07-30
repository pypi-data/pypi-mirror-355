#
# import ee
# ee.Initialize()
#
# # Define your region of interest (replace with your area if needed)
# region = ee.Geometry.Rectangle([60, 23, 80, 38])  # Example: Pakistan
#
# # Time range
# start_year = 2000
# end_year = 2025
#
# # Load MODIS Terra Daily Snow Cover
# modis = ee.ImageCollection("MODIS/061/MOD10A1")
#
# # Step 1: QA and valid snow cover filtering
# def apply_snow_qa_mask(image):
#     snow = image.select('NDSI_Snow_Cover')
#     qa = image.select('NDSI_Snow_Cover_Basic_QA')
#
#     # Mask invalid snow values (outside 0–100)
#     snow = snow.updateMask(snow.gte(0).And(snow.lte(100)))
#
#     # Accept only QA values: 0 (Best), 1 (Good), 2 (OK)
#     qa_valid = qa.eq(0).Or(qa.eq(1)).Or(qa.eq(2))
#     snow = snow.updateMask(qa_valid)
#
#     return snow.copyProperties(image, image.propertyNames())
#
# # Apply the mask to the image collection
# modis_clean = modis.map(apply_snow_qa_mask)
#
# # Step 2: Function to compute monthly average snow cover
# def get_monthly_snow_avg(year, month):
#     start = ee.Date.fromYMD(year, month, 1)
#     end = start.advance(1, 'month')
#
#     monthly = modis_clean.filterDate(start, end).filterBounds(region)
#
#     # Reduce daily snow cover to monthly average
#     monthly_avg = monthly.reduce(ee.Reducer.mean()).clip(region)
#
#     return monthly_avg.set({
#         'year': year,
#         'month': month,
#         'system:time_start': start.millis()
#     })
#
# # Step 3: Loop through years and months to generate ImageCollection
# monthly_images = []
# for year in range(start_year, end_year + 1):
#     for month in range(1, 13):
#         monthly_img = get_monthly_snow_avg(year, month)
#         monthly_images.append(monthly_img)
#
# monthly_snow_ic = ee.ImageCollection(monthly_images)
#
# # Print number of images generated
# print("Total monthly images:", len(monthly_images))
#
# # Optional: Export a single month (e.g., January 2023)
# sample = monthly_snow_ic.filter(ee.Filter.eq('year', 2023)) \
#     .filter(ee.Filter.eq('month', 1)) \
#     .first()
#
# task = ee.batch.Export.image.toDrive(
#     image=sample,
#     description='MODIS_SnowCover_Jan2023',
#     folder='GEE_Exports',
#     fileNamePrefix='snowcover_2023_01',
#     region=region.coordinates(),
#     scale=500,
#     maxPixels=1e13
# )
# task.start()
