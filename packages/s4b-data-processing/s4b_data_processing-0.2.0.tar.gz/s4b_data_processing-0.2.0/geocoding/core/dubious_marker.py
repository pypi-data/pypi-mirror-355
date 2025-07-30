import pandas as pd
from tqdm import tqdm
from transliterate import translit


def dubious_marker(delta_addr_cn):
    delta_addr_cn["lat_ya"] = None
    delta_addr_cn["lon_ya"] = None
    delta_addr_cn["lat"] = None
    delta_addr_cn["lon"] = None
    delta_addr_cn["dubious_ya"] = None
    delta_addr_cn["dubious_nspd"] = None
    from geopy.distance import geodesic


    for id, geo_req in tqdm(delta_addr_cn.iterrows(), total=len(delta_addr_cn)):
        name_ya = geo_req["name_hc"]
        lat_ya_addr = geo_req["lat_ya_addr"]
        lon_ya_addr = geo_req["lon_ya_addr"]
        lat_ya_hc = geo_req["lat_ya_hc"]
        lon_ya_hc = geo_req["lon_ya_hc"]
        lat_nspd = geo_req["lat_nspd"]
        lon_nspd = geo_req["lon_nspd"]
        lat_nspd_near = geo_req["lat_nspd_near"]
        lon_nspd_near = geo_req["lon_nspd_near"]

        lat = None
        lon = None
        lat_ya = None
        lon_ya = None
        dubious_ya = None
        dubious_nspd = None

        is_hc_nan = False
        if not pd.isnull(name_ya):
            name_ya = name_ya.lower().strip().replace('ё', "е")
            name_proj_wo_hc = geo_req["Проект"].lower().strip().replace('ё', "е").replace("жк", "").replace("жилой комплекс", "")
            name_ya_wo_hc = name_ya.replace("жк", "").replace("жилой комплекс", "")

            hc_names_match = (name_proj_wo_hc in name_ya_wo_hc) or (name_ya_wo_hc in name_proj_wo_hc) or (name_ya_wo_hc in translit(name_proj_wo_hc, "ru")) or (translit(name_proj_wo_hc, "ru") in name_ya_wo_hc)
            hc_match = ("жк" in name_ya) or ("жилой комплекс" in name_ya) or ("жилой квартал" in name_ya)
            if hc_names_match or hc_match:
                lat_ya = lat_ya_hc
                lon_ya = lon_ya_hc
        else:
            is_hc_nan = True


        if not pd.isnull(lat_ya_addr):
            if not is_hc_nan:
                if geodesic((lat_ya_hc, lon_ya_hc), (lat_ya_addr, lon_ya_addr)) < 3:
                    if hc_names_match:
                        dubious_ya = 0
                    elif hc_match:
                        dubious_ya = 3
                    else:
                        dubious_ya = 6
                        lat_ya = lat_ya_addr
                        lon_ya = lon_ya_addr
                else:
                    if hc_names_match:
                        dubious_ya = 1
                    elif hc_match:
                        dubious_ya = 4
                    else:
                        dubious_ya = 7
                        lat_ya = lat_ya_addr
                        lon_ya = lon_ya_addr
            else:
                dubious_ya = 9
                lat_ya = lat_ya_addr
                lon_ya = lon_ya_addr
        else:
            if not is_hc_nan:
                if hc_names_match:
                    dubious_ya = 2
                elif hc_match:
                    dubious_ya = 5
                else:
                    dubious_ya = 8

        if not pd.isnull(lat_nspd):
            lat = lat_nspd
            lon = lon_nspd
            if lat_ya is not None:
                if geodesic((lat, lon), (lat_ya, lon_ya)) < 3:
                    dubious_nspd = 0
                else:
                    dubious_nspd = 2
            else:
                dubious_nspd = 1
        else:
            if not pd.isnull(lat_nspd_near):
                lat = lat_nspd_near
                lon = lon_nspd_near
                if lat_ya is not None:
                    if geodesic((lat_nspd_near, lon_nspd_near), (lat_ya, lon_ya)) < 3:
                        lat = lat_ya
                        lon = lon_ya
                        dubious_nspd = 3
                    else:
                        dubious_nspd = 5
                else:
                    dubious_nspd = 4
            else:
                dubious_nspd = 6
                lat = lat_ya
                lon = lon_ya
        delta_addr_cn.loc[id, "lat"] = lat
        delta_addr_cn.loc[id, "lon"] = lon
        delta_addr_cn.loc[id, "lat_ya"] = lat_ya
        delta_addr_cn.loc[id, "lon_ya"] = lon_ya
        delta_addr_cn.loc[id, "dubious_ya"] = dubious_ya
        delta_addr_cn.loc[id, "dubious_nspd"] = dubious_nspd
    dubious_ya_map = {0: "ya_hc", 3: "ya_hc", 6: "ya_hc", 1: "ya_hc", 4: "ya_hc", 7: "ya_addr", 9: "ya_addr", 2: "ya_hc",
                      5: "ya_hc", 8: "ya_hc"}

    dubious_nspd_map = {0: "cn", 2: "cn", 1: "cn", 3: "cn_near", 4: "cn_near", 5: "cn_near", 6: "ya"}
    delta_addr_cn["how_ya"] = delta_addr_cn["dubious_ya"].map(dubious_ya_map)
    delta_addr_cn["how_nspd"] = delta_addr_cn["dubious_nspd"].map(dubious_nspd_map)
    delta_addr_cn["how"] = delta_addr_cn["how_nspd"]
    is_how_ya = delta_addr_cn["how"].isnull()
    delta_addr_cn.loc[is_how_ya, "how"] = delta_addr_cn.loc[is_how_ya, "how_ya"]

