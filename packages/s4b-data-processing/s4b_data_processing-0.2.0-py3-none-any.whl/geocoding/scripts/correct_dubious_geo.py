import pickle
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

data_dir = Path(input("Введите абсолютный путь к директории с данными: ")) # передача абсолютного пути к директории "data"
region_name = input("Введите название директории с данными региона, например, nsk: ")
region_data_dir = data_dir / "regions" / region_name
geolocations_dir = region_data_dir / "geolocations"
coordinates_path = geolocations_dir / "coordinates.pkl"


if not geolocations_dir.exists() or not coordinates_path.exists():
    print("Сначала запустите скрипт с геокодингом.")
    exit()

coordinates = pickle.loads(coordinates_path.read_bytes())

fig1 = px.imshow(pd.crosstab(coordinates["dubious_ya"].astype(str), coordinates["dubious_nspd"].astype(str), dropna=False), text_auto=True)#.write_image(geolocations_dir / "dubious_count.png", scale=3)
fig2 = px.imshow(pd.crosstab(coordinates["dubious_ya"].astype(str), coordinates["dubious_nspd"].astype(str), dropna=False), text_auto=True)
fig2 = go.Figure(fig2.data, fig2.layout)
fig2 = fig2.update_traces(text=pd.crosstab(coordinates["dubious_ya"].astype(str), coordinates["dubious_nspd"].astype(str), values=coordinates["how"], aggfunc=pd.Series.mode, dropna=False).values, texttemplate="%{text}", hovertemplate=None)
fig1.show()
fig2.show()
#fig2.write_image(data_dir_region / "geolocations" / "dubious_how.png", scale=3)

print("\nВыберите группы сомнительных геоточек, которые хотите исправить.")
fix_ya = list(map(str.strip, input("Напишите номера сомнительных геокоординат через запятую по яндексу (None включен автоматически): ").split(","))) + ["None"]
fix_nspd = list(map(str.strip, input("Напишите номера сомнительных геокоординат через запятую по кадастровым номерам (None включен автоматически): ").split(","))) + ["None"]
dubious_req = coordinates[(coordinates["dubious_ya"].astype(str).isin(fix_ya) & coordinates["dubious_nspd"].astype(str).isin(fix_nspd) & ~coordinates["is_checked"]) | coordinates[["lat", "lon"]].isna().any(axis=1)]

print("\nЗайдите на https://yandex.ru/maps/ и введите в поиске координаты. Если они Вас устраивают, то оставьте ввод пустым, иначе введите новые широту и долготу через запятую. Для завершения исправлений введите exit().")
for id, row in dubious_req.iterrows():
    print(row["Проект"], row["Город"], row["Адрес корпуса"], row["lat"], row["lon"], row["how"])
    geo_input = input()
    if not geo_input.strip():
        coordinates.loc[id, "is_checked"] = True
    elif len(geo_input.split(",")) == 2:
        lat, lon = map(float, geo_input.split(","))
        coordinates.loc[id, ("lat", "lon")] = lat, lon
        coordinates.loc[id, "is_checked"] = True
    elif geo_input == "exit()":
        break

coordinates_path.write_bytes(pickle.dumps(coordinates))
print("Новые координаты сохранены")