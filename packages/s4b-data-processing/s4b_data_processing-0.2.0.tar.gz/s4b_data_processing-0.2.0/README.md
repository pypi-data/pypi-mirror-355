# Репозиторий data-processing

Репозиторий содержит функции геокодирования и предобработки исходных данных от BNMAP.

## 1. Структура репозитория
```
📦 s4b-data-processing
 ┣ 📂 geocoding
 ┃ ┣ 📂 core
 ┃ ┃ ┣ 📜 dubious_marker.py
 ┃ ┃ ┣ 📜 exceptions.py
 ┃ ┃ ┣ 📜 geocoder.py
 ┃ ┃ ┣ 📜 utils.py
 ┃ ┃ ┣ 📜 yandex_modified.py
 ┃ ┃ ┗ 📜 __init__.py
 ┃ ┣ 📂 scripts
 ┃ ┃ ┣ 📜 correct_dubious_geo.py
 ┃ ┃ ┣ 📜 geocode.py
 ┃ ┃ ┣ 📜 update_market_deals.py
 ┃ ┃ ┣ 📜 ya_api_keys.csv
 ┃ ┃ ┗ 📜 __init__.py
 ┃ ┗ 📜 __init__.py
 ┣ 📂 preprocessing
 ┃ ┣ 📜 preprocessing.py
 ┃ ┣ 📜 features.py
 ┃ ┣ 📜 utils.py
 ┃ ┗ 📜 __init__.py
 ┣ 📜 preprocessing_example.ipynb
 ┣ 📜 requirements.txt
 ┣ 📜 README.md
 ┗ 📜 __init__.py
```

## 2. Первичный сбор гео-координат домов в регионе
Необходимо наличие директории `data` с данными по регионам и со следующей структурой:
```
📂data
 ┣ 📂regions
 ┃ ┣ 📂ekb
 ┃ ┣ 📂msk
 ┃ ┃ ┣ 📂market_deals
 ┃ ┃ ┃ ┣ файл_со_сделками.parquet
 ┃ ┃ ┃ ┗ или файл_со_сделками.xlsx
 ┃ ┃ ┗ 📂project_declarations
 ┃ ┃   ┣ файл_с_проектными_декларациями.parquet
 ┃ ┃   ┗ или файл_с_проектными_декларациями.xlsx
 ┃ ┗ 📂nsk
 ┗ 📜__init__.py
```

Для запуска первичного сбора гео-координат запустите через консоль скрипт `geocode.py`:
```shell
python -m scripts.geocode
```
Вам могут понадобиться границы поиска гео-координат:
```
United MSK: 35.203810,54.167977~40.624199,56.982672
United NSK: 74.312415,57.654077~86.551184,52.812563
EKB: 60.326783, 56.985508~60.942358, 56.634953
```

**Везде далее необходимо наличие директории `data` с данными по регионам и со следующей структурой:**
```
📂data
 ┣ 📂preprocessing
 ┣ 📂regions
 ┃ ┣ 📂ekb
 ┃ ┣ 📂msk
 ┃ ┃ ┣ 📂geolocations  
 ┃ ┃ ┃ ┣ 📜bbox.txt
 ┃ ┃ ┃ ┣ 📜coordinates.pkl 
 ┃ ┃ ┃ ┗ 📜near_nspd.pkl   
 ┃ ┃ ┣ 📂market_deals
 ┃ ┃ ┃ ┣ 📜сделки.parquet
 ┃ ┃ ┃ ┗ 📜сделки.xlsx
 ┃ ┃ ┗ 📂project_declarations
 ┃ ┃   ┣ 📜проектные декларации.parquet
 ┃ ┃   ┗ 📜проектные декларации.xlsx
 ┃ ┗ 📂nsk
 ┗ 📜__init__.py
```
Директория `geolocations` c необходимыми файлами будет создана после первичного сбора гео-координат.

## 3. Обновление гео-координат домов в регионе
Для запуска обновления гео-координат запустите через консоль скрипт `geocode.py`:
```shell
python -m scripts.geocode
```
## 4. Исправление сомнительных гео-координат домов в регионе
Чтобы исправить сомнительные гео-координаты запустите через консоль скрипт `correct_dubious_geo.py`:
```shell
python -m scripts.correct_dubious_geo
```
## 5. Слияние необработанных сделок с гео-координатами
Чтобы получить сделки с гео-коориднатами запустите через консоль скрипт `update_market_deals.py`:
```shell
python -m scripts.update_market_deals
```

## 6. Предобработка данных
Пример предобработки данных приведён в ноутбуке `preprocessing_example.ipynb`.
