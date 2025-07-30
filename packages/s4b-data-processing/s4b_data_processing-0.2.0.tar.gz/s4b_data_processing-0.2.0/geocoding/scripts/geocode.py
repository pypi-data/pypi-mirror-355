import pandas as pd
import numpy as np
from numpy import dtype
import pickle
from core.geocoder import geocoder
from core.dubious_marker import dubious_marker

from pathlib import Path

script_path = Path(__file__)
ya_api_keys = pd.read_csv(script_path.parent / "ya_api_keys.csv")["key"].to_list()

data_dir = Path(input("Введите абсолютный путь к директории с данными: ")) # передача абсолютного пути к директории "data"
region_name = input("Введите название директории с данными региона, например, nsk: ").strip()
region_data_dir = data_dir / "regions" / region_name
geolocations_dir = region_data_dir / "geolocations"
geolocations_dir.mkdir(parents=True, exist_ok=True)

bbox_path = geolocations_dir / "bbox.txt"
coordinates_path = geolocations_dir / "coordinates.pkl"
near_nspd_path = geolocations_dir / "near_nspd.pkl"

if bbox_path.exists():
    bbox = bbox_path.read_text()
else:
    bbox = input("Введите границы поиска в формате: долгота, широта левой верхней вершины~долгота, широта правой нижней вершины. Например, для Екатеринбурга 60.326783, 56.985508~60.942358, 56.634953: ")
    bbox_path.write_text(bbox, encoding="utf-8")


columns = ['ID проекта', 'ID корпуса', 'Проект', 'Город', 'Адрес корпуса', 'Кадастровый номер', 'lat_ya_hc',
           'lon_ya_hc', 'lat_ya_addr', 'lon_ya_addr', 'kind_hc', 'kind_addr',
           'locality_hc', 'locality_addr', 'name_hc', 'name_addr', 'addr_hc',
           'addr_addr', 'lat_nspd', 'lon_nspd', 'lat_nspd_near', 'lon_nspd_near',
           'err_nspd', 'err_nspd_near', 'err_ya', 'lat_ya', 'lon_ya', 'lat', 'lon',
           'dubious_ya', 'dubious_nspd', 'how_ya', 'how_nspd', 'how',
           'is_checked']
dtypes = {'Проект': dtype('O'),
          'Город': dtype('O'),
          'Адрес корпуса': dtype('O'),
          'Кадастровый номер': dtype('O'),
          'lat_ya_hc': dtype('float64'),
          'lon_ya_hc': dtype('float64'),
          'lat_ya_addr': dtype('float64'),
          'lon_ya_addr': dtype('float64'),
          'kind_hc': dtype('O'),
          'kind_addr': dtype('O'),
          'locality_hc': dtype('O'),
          'locality_addr': dtype('O'),
          'name_hc': dtype('O'),
          'name_addr': dtype('O'),
          'addr_hc': dtype('O'),
          'addr_addr': dtype('O'),
          'lat_nspd': dtype('float64'),
          'lon_nspd': dtype('float64'),
          'lat_nspd_near': dtype('float64'),
          'lon_nspd_near': dtype('float64'),
          'err_nspd': dtype('O'),
          'err_nspd_near': dtype('O'),
          'err_ya': dtype('bool'),
          'lat_ya': dtype('O'),
          'lon_ya': dtype('O'),
          'lat': dtype('O'),
          'lon': dtype('O'),
          'dubious_ya': dtype('O'),
          'dubious_nspd': dtype('O'),
          'how_ya': dtype('O'),
          'how_nspd': dtype('O'),
          'how': dtype('O'),
          'is_checked': dtype('bool')}

if coordinates_path.exists():
    coordinates_old = pickle.loads(coordinates_path.read_bytes())
else:
    coordinates_old = pd.DataFrame(columns=columns).set_index(['ID проекта', 'ID корпуса']).astype(dtypes)
    coordinates_old.index = coordinates_old.index.set_levels([
        coordinates_old.index.levels[0].astype(dtype('O')),
        coordinates_old.index.levels[1].astype(dtype('O'))
    ])

if near_nspd_path.exists():
    near_nspd = pickle.loads(near_nspd_path.read_bytes())
else:
    near_nspd = {}

print("\nФайлы со сделками:")
market_deals_files = list((region_data_dir / "market_deals").glob("*.parquet"))
market_deals_files += list((region_data_dir / "market_deals").glob("*.xlsx"))
market_deals_files.sort(key=lambda x: -x.stat().st_mtime)
for i, path in enumerate(market_deals_files):
    print(f"{i+1}. {path.name}")
market_deals_num = int(input("\nВведите номер файла со сделками: "))
market_deals_file = market_deals_files[market_deals_num - 1]
if market_deals_file.suffix == ".parquet":
    market_deals = pd.read_parquet(market_deals_file)
elif market_deals_file.suffix == ".xlsx":
    print("Файл Excel загружается.")
    market_deals = pd.read_excel(market_deals_file)
    market_deals.to_parquet(region_data_dir / "market_deals" / f"{market_deals['Дата договора'].max().strftime('%Y_%m')}.parquet")
else:
    print("Невозможно открыть файл с таким расширением.")
    exit()

print("\nФайлы с проектными декларациями:")
pd_files = list((region_data_dir / "project_declarations").glob("*.parquet"))
pd_files += list((region_data_dir / "project_declarations").glob("*.xlsx"))
pd_files.sort(key=lambda x: -x.stat().st_mtime)
for i, path in enumerate(pd_files):
    print(f"{i+1}. {path.name}")
pd_num = int(input("\nВведите номер файла с проектными декларациями: "))
pd_data_file = pd_files[pd_num - 1]
if pd_data_file.suffix == ".parquet":
    pd_data = pd.read_parquet(pd_data_file)
elif pd_data_file.suffix == ".xlsx":
    print("Файл Excel загружается.")
    pd_data = pd.read_excel(pd_data_file)
    pd_data.to_parquet(region_data_dir / "project_declarations" / f"{market_deals['Дата договора'].max().strftime('%Y_%m')}.parquet")
else:
    print("Невозможно открыть файл с таким расширением.")
    exit()

cadastral_numbers = pd_data.groupby(["ID проекта", "ID корпуса"])["Номер регистрации"].apply(
    lambda x: x.str.extract('(\\d+:\\d+:\\d+(?::\\d+)?)').drop_duplicates()[0].to_list()).to_frame().rename(columns={"Номер регистрации": "Кадастровый номер"})

cadastral_numbers = cadastral_numbers["Кадастровый номер"].apply(lambda x: np.nan if pd.isnull(x)[0] and len(x) == 1 else x)
deals_houses = market_deals.groupby(["ID проекта", "ID корпуса"])[["Проект", "Город", "Адрес корпуса"]].agg(lambda x: x.mode())
addr_cn = deals_houses.merge(cadastral_numbers, on=["ID проекта", "ID корпуса"], how="left")

# Смоделируем ситуацию, когда пришли новые данные
# coordinates_old = coordinates.drop(coordinates.sample(10).index)
delta_addr_cn = addr_cn[~addr_cn.index.isin(coordinates_old.index)].copy()
print(f"\nНайдено {len(delta_addr_cn)} не геокодированных домов.")
if not len(delta_addr_cn):
    exit()

geocoder(bbox, ya_api_keys, near_nspd, delta_addr_cn)
dubious_marker(delta_addr_cn)

delta_addr_cn["is_checked"] = False
coordinates_new = pd.concat([coordinates_old, delta_addr_cn])
coordinates_path.write_bytes(pickle.dumps(coordinates_new))
near_nspd_path.write_bytes(pickle.dumps(near_nspd))
print("Новые координаты сохранены")

