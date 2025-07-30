import pickle
from pathlib import Path

import pandas as pd

data_dir = Path(input("Введите абсолютный путь к директории с данными: ")) # передача абсолютного пути к директории "data"
region_name = input("Введите название директории с данными региона, например, nsk: ").strip()
region_data_dir = data_dir / "regions" / region_name
geolocations_dir = region_data_dir / "geolocations"
coordinates_path = geolocations_dir / "coordinates.pkl"

if not geolocations_dir.exists() or not coordinates_path.exists():
    print("Сначала запустите скрипт с геокодингом.")
    exit()

market_deals_files = list((region_data_dir / "market_deals").glob("*.parquet"))
market_deals_files.sort(key=lambda x: -x.stat().st_mtime)
for i, path in enumerate(market_deals_files):
    print(f"{i+1}. {path.name}")
market_deals_num = int(input("\nВведите номер файла со сделками: "))

market_deals_file = market_deals_files[market_deals_num - 1]
market_deals = pd.read_parquet(market_deals_file)
coordinates = pickle.loads(coordinates_path.read_bytes())

market_deals = (market_deals.merge(coordinates[["lat", "lon"]], on=["ID проекта", "ID корпуса"], how="left")
                .rename(columns={"lat": "latitude", "lon": "longitude"}))

geo_market_deals_path = market_deals_file.parent / f"geo_{market_deals_file.name}"
market_deals.to_parquet(geo_market_deals_path)
print(f"Данные по сделкам с координатами успешно сохранены в файл {geo_market_deals_path.name}")