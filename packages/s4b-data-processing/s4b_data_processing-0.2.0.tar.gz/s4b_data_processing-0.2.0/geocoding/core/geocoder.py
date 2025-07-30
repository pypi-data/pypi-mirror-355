import numpy as np
import pandas as pd
from tqdm import tqdm
from shapely import MultiPoint
from core import headers_nspd
from .yandex_modified import Yandex
from .utils import *


def geocoder(bbox, ya_api_keys, near_nspd, delta_addr_cn):
    api_key_number = 0
    geolocator = Yandex(ya_api_keys[api_key_number])
    delta_addr_cn["err_nspd"] = False
    delta_addr_cn["err_nspd_near"] = False
    delta_addr_cn["err_ya"] = False
    number_of_requests = [0] * len(ya_api_keys)

    for id, house in tqdm(delta_addr_cn.iterrows(), total=len(delta_addr_cn)):
        project = house["Проект"]
        city = house["Город"]
        address = house["Адрес корпуса"]
        cn_list = house["Кадастровый номер"]

        lat_ya_hc = None
        lon_ya_hc = None

        lat_ya_addr = None
        lon_ya_addr = None

        kind_hc = None
        kind_addr = None

        locality_hc = None
        locality_addr = None

        name_hc = None
        name_addr = None

        addr_addr = None
        addr_hc = None

        lat_nspd = None
        lon_nspd = None

        lat_nspd_near = None
        lon_nspd_near = None

        while True:
            try:
                query_proj = f"{city}, ЖК {project}" # More representative
                res_proj = geolocator.geocode(query_proj, bbox=bbox)
                number_of_requests[api_key_number] += 1
                if number_of_requests[api_key_number] % 100 == 0:
                    api_key_number = (api_key_number + 1) % len(ya_api_keys)

                query_addr = f"{city}, {address}"

                res_addr = geolocator.geocode(query_addr, bbox=bbox)
                number_of_requests[api_key_number] += 1
                if number_of_requests[api_key_number] % 100 == 0:
                    api_key_number = (api_key_number + 1) % len(ya_api_keys)

                if res_proj is not None:
                    lat_ya_hc = res_proj.latitude
                    lon_ya_hc = res_proj.longitude
                    kind_hc = get_kind_ya_raw(res_proj)
                    locality_hc = get_locality_ya_raw(res_proj)
                    name_hc = get_name_ya_raw(res_proj)
                    addr_hc = res_proj.address

                if res_addr is not None:
                    lat_ya_addr = res_addr.latitude
                    lon_ya_addr = res_addr.longitude
                    kind_addr = get_kind_ya_raw(res_addr)
                    locality_addr = get_locality_ya_raw(res_addr)
                    name_addr = get_name_ya_raw(res_addr)
                    addr_addr = res_addr.address

                break
            except Exception as e:
                if api_key_number == (len(ya_api_keys) - 1):
                    delta_addr_cn.loc[id, "err_ya"] = True
                    api_key_number = 0
                    break
                api_key_number = (api_key_number + 1) % len(ya_api_keys)
                geolocator = Yandex(ya_api_keys[api_key_number])

        if cn_list is not np.nan:
            nspd_locations = []
            how = "nspd"
            for cn in cn_list:
                if pd.isnull(cn):
                    continue
                try:
                    location = geo_by_nspd(cn, headers_nspd)
                except Exception as e:
                    delta_addr_cn.loc[id, "err_nspd"] = True
                    continue
                nspd_locations.append(location)

            if nspd_locations:
                nspd_centroid = MultiPoint(nspd_locations).centroid
                lat_nspd = nspd_centroid.y
                lon_nspd = nspd_centroid.x


            near_locations = []
            for i in range(10):
                for cn in cn_list:
                    if pd.isnull(cn):
                        continue
                    near_cn = cn[:-1] + str(i)
                    try:
                        if near_cn not in near_nspd:
                            location = geo_by_nspd(near_cn, headers_nspd)
                            near_nspd[near_cn] = location

                    except Exception as e:
                        delta_addr_cn.loc[id, "err_nspd_near"] = True
                        continue
                    if near_nspd[near_cn] not in near_locations:
                        near_locations.append(near_nspd[near_cn])

            if near_locations:
                near_centroid = MultiPoint(near_locations).centroid
                lat_nspd_near = near_centroid.y
                lon_nspd_near = near_centroid.x

        delta_addr_cn.loc[id, "lat_ya_hc"] = lat_ya_hc
        delta_addr_cn.loc[id, "lon_ya_hc"] = lon_ya_hc
        delta_addr_cn.loc[id, "lat_ya_addr"] = lat_ya_addr
        delta_addr_cn.loc[id, "lon_ya_addr"] = lon_ya_addr
        delta_addr_cn.loc[id, "kind_hc"] = kind_hc
        delta_addr_cn.loc[id, "kind_addr"] = kind_addr
        delta_addr_cn.loc[id, "locality_hc"] = locality_hc
        delta_addr_cn.loc[id, "locality_addr"] = locality_addr
        delta_addr_cn.loc[id, "name_hc"] = name_hc
        delta_addr_cn.loc[id, "name_addr"] = name_addr
        delta_addr_cn.loc[id, "addr_hc"] = addr_hc
        delta_addr_cn.loc[id, "addr_addr"] = addr_addr
        delta_addr_cn.loc[id, "lat_nspd"] = lat_nspd
        delta_addr_cn.loc[id, "lon_nspd"] = lon_nspd
        delta_addr_cn.loc[id, "lat_nspd_near"] = lat_nspd_near
        delta_addr_cn.loc[id, "lon_nspd_near"] = lon_nspd_near