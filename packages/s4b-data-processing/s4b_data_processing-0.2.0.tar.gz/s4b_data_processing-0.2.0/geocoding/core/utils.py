import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import geopandas as gpd

from .exceptions import BadRequestGeoException


def get_kind_ya_raw(location):
    kind = None
    if "kind" in location.raw["metaDataProperty"]["GeocoderMetaData"]:
        kind = location.raw["metaDataProperty"]["GeocoderMetaData"]["kind"]
    return kind


def get_name_ya_raw(location):
    name = None
    if "name" in location.raw:
        name = location.raw["name"]
    return name


def get_locality_ya_raw(location):
    locality = None
    for comp in location.raw["metaDataProperty"]["GeocoderMetaData"]["Address"]["Components"]:
        if comp["kind"] == "locality":
            locality = comp["name"]
    return locality


def geo_by_nspd(cadastral_num, headers):
    response = requests.get(f"https://nspd.gov.ru/api/geoportal/v2/search/geoportal?query={cadastral_num}&thematicSearchId=1", headers=headers, verify=False)
    if response.status_code != 200:
        raise BadRequestGeoException(response)
    gpd_json = response.json()
    geo_centroid = gpd.GeoDataFrame.from_features(gpd_json["data"]["features"]).set_crs(epsg=3857).centroid.to_crs(epsg=4326)[0]
    return geo_centroid