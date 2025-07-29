import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

def prioritize_mask_and_clip(gdf_list, attribute, ascending=True):
    # Combine all with a marker for origin
    gdf_all = []
    for idx, gdf in enumerate(gdf_list):
        temp = gdf.copy()
        temp['_src_idx'] = idx
        gdf_all.append(temp)
    all_gdf = gpd.GeoDataFrame(pd.concat(gdf_all, ignore_index=True), crs=gdf_list[0].crs)

    all_gdf = all_gdf.sort_values(attribute, ascending=ascending).reset_index(drop=True)

    claimed = None
    out_gdfs = [[] for _ in range(len(gdf_list))]

    for _, row in all_gdf.iterrows():
        geom = row.geometry
        if claimed is not None:
            geom = geom.difference(claimed)
        if not geom.is_empty:
            new_row = row.copy()
            new_row.geometry = geom
            out_gdfs[row._src_idx].append(new_row)
            claimed = unary_union([claimed, geom]) if claimed is not None else geom

    orig_cols = gdf_list[0].columns
    result = []
    for group in out_gdfs:
        if group:
            temp_gdf = gpd.GeoDataFrame(group, columns=all_gdf.columns, crs=gdf_list[0].crs)
            result.append(temp_gdf[orig_cols].reset_index(drop=True))
        else:
            result.append(gdf_list[0][0:0].copy())
    return result
