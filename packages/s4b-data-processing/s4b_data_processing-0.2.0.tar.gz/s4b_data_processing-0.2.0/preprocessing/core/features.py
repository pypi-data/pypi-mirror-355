import typing as tp

import geopy.distance as gpd
import numpy as np
import pandas as pd

from .utils import relative_number_type


def drop_nan(deals: pd.DataFrame, quantile_level: tp.Optional[float] = 0.5) -> pd.DataFrame:
    """
    Убирает NaN в столбце «Заявленный срок ввода в эксплуатацию», заполняя их значением "Старт продаж" + квантиль для
    (df["Заявленный срок ввода в эксплуатацию"] - df["Старт продаж"])\n
    Важно: В "Старт продаж" NaN быть уже не должно -> start_of_sales запускается перед date_of_exploitation

    :param deals: Данные о сделках.
    :param quantile_level: Уровень квантиля
    :return: Копия сделок с NaN, которые заменили определенными значениями
    """
    deals = deals.copy()
    deals = deals[deals["Проект"] != "Квартал Пригородный простор 2.0"]

    df = deals.copy().dropna(subset=["Заявленный срок ввода в эксплуатацию"])
    df["diff"] = pd.to_datetime(df["Заявленный срок ввода в эксплуатацию"]) - df["Старт продаж"]
    df["quantiles"] = df.groupby("Проект")["diff"].transform(lambda x: x.quantile(quantile_level))

    dict_ = df[["Проект", "quantiles"]].set_index("Проект").to_dict()['quantiles']
    deals["quantiles"] = deals["Проект"].map(dict_)

    deals["Заявленный срок ввода в эксплуатацию"] = deals["Заявленный срок ввода в эксплуатацию"].fillna(
        value=(deals["quantiles"] + deals["Старт продаж"]))

    deals = deals.drop(["quantiles"], axis=1)
    return deals


def distance_to_point(deals: pd.DataFrame, lat: float, lon: float) -> pd.DataFrame:
    """
    Добавляет в признак с расстоянием(km) до заданной точки.

    :param deals: Данные о сделках с англоязычными признаками.
    :param lat: Широта
    :param lon: Долгота
    :return: Данные о сделках с новым признаком
    """
    deals = deals.copy()
    deals["distance_to_point"] = deals.apply(lambda x: gpd.distance((lat, lon), (x.latitude, x.longitude)).km, axis=1)
    return deals


def contract_date(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Ничего не делает с признаком «Дата сделки».
    Возможно, функция нужна для целостности картины об оставленных признаках.

    :param deals: Данные о сделках.
    :return: Неизмененный deals.
    """
    deals["Дата договора"] = pd.to_datetime(deals["Дата договора"])
    return deals


def deal_type(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Конвертирует признак «Тип сделки» в uint8, по следующему правилу:
    «Договор участия» → 0
    «Договор уступки» → 1
    Предполагается, что признак не содержит пропущенные данные.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Тип сделки».
    """
    deals = deals.copy()
    deals["Тип сделки"] = (deals["Тип сделки"] == "Договор уступки").astype(np.uint8)
    return deals


def floor(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Конвертирует признак «Этаж» в int8.\n
    Если значение в признаке неприводимое (NaN, строки без цифр), то сделка удаляется.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Этаж».
    """
    deals = deals.copy()
    deals["Этаж"] = pd.to_numeric(deals["Этаж"], errors="coerce")
    deals = deals[np.isfinite(deals["Этаж"])].reset_index(drop=True)
    deals["Этаж"] = deals["Этаж"].astype(np.int8)
    return deals


def number_rooms(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Конвертирует признак «Количество комнат» в int8, заменяя «ст.» на 0.\n
    Если значение в признаке неприводимое (NaN, строки без цифр), то сделка удаляется.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Количество комнат».
    """
    deals = deals.copy()
    deals["Количество комнат"] = deals["Количество комнат"].str.replace("ст", "0")
    deals["Количество комнат"] = pd.to_numeric(deals["Количество комнат"], errors="coerce")
    deals = deals[np.isfinite(deals["Количество комнат"])].reset_index(drop=True)
    deals["Количество комнат"] = deals["Количество комнат"].astype(np.int8)
    return deals


def estate_type(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Высчитывает следующие относительные частоты для каждого типа:\n
    «Паркинг» = #машино-места / #квартир в корпусе\n
    «Кладовые» = #кладовые / #квартир в корпусе\n
    Если нет сделок на квартиры в корпусе, то поле заполняется значением np.nan.

    :param deals: Данные о сделках.
    :return: Копия сделок с новыми признаками в которой удалены признак «Тип объекта» и сделки не на квартиры.
    """
    deals = deals.copy()
    project_building_groups = deals.groupby(["Проект", "ID корпуса"])
    deals["Паркинг"] = project_building_groups["Тип объекта"].transform(
        lambda x: relative_number_type(x, "машино-место", "квартира"))
    deals["Кладовые"] = project_building_groups["Тип объекта"].transform(
        lambda x: relative_number_type(x, "кладовка", "квартира"))
    deals = deals[deals["Тип объекта"] == "квартира"].reset_index(drop=True)
    del deals["Тип объекта"]
    return deals


def corpus_id(deals: pd.DataFrame,
              save_old: bool = True) -> pd.DataFrame:
    """
    Кодирует признак «ID корпуса» целыми числами по частоте встречаемости начиная с нуля.
    Пример: pd.Series(['a','c','b','c','b','c']) -> pd.Series([2,0,1,0,1,0])

    :param deals: Данные о сделках.
    :param save_old: Сохранять ли необработанные данные.
    :return: Копия сделок с преобразованным признаком «ID корпуса».
    """
    freq_dct = deals['ID корпуса'].value_counts().to_dict()
    encoding_dict = {}
    for i, (item, freq) in enumerate(sorted(freq_dct.items(), key=lambda x: x[1], reverse=True)):
        encoding_dict[item] = i
    if save_old:
        deals["house_id_old"] = deals["ID корпуса"]
    deals["ID корпуса"] = deals["ID корпуса"].map(encoding_dict)
    return deals


def project(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Ничего не делает.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Проект».
    """
    deals = deals.copy()
    deals['Проект'] = deals['Проект'].astype(str)
    return deals


def location(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Кодирует значения столбца «Локация» в порядке убывания их количества.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Локация».
    """
    deals = deals.copy()
    value_counts = deals['Локация'].value_counts().sort_values(ascending=False)
    encoding = {location: idx for idx, location in enumerate(value_counts.index)}
    deals['Локация'] = deals['Локация'].map(encoding)
    return deals


def district(deals: pd.DataFrame,
             by="Район",
             target="Цена за кв. метр",
             is_ml=False,
             save_old=True) -> tp.Union[pd.DataFrame, tuple[pd.DataFrame, dict[tp.Any, int]]]:
    """
    Кодирует столбец «Район» целыми числами в зависимости от убывания средней цены (по столбцу «Цена за кв. метр»)
    начиная с нуля.
    Важно: Предполагается, что столбец «Цена за кв. метр» уже преобразован.

    :param deals: Данные о сделках.
    :param by: столбец, который упорядочиваем.
    :param target: характеристика, по которой упорядочиваются районы.
    :param is_ml: аргумент, отвечающий за цели предобработки данных. Если для
    :param save_old: сохранять ли первоначальный столбец (только при is_ml=True)
    алгоритмов предсказания цены - то работает слегка иначе.
    :return: Копия сделок с преобразованным признаком «Район».
    """
    deals = deals.copy()
    if save_old:
        deals["district_old"] = deals[by]
    grouped = deals.groupby(by=by)[target].mean()
    sorted_grouped = grouped.sort_values(ascending=False)
    encoding_dict = {val: i for i, val in enumerate(sorted_grouped.index)}
    deals[by] = deals[by].map(encoding_dict)
    deals = deals[deals[by].notna()]
    deals = deals.astype({by: int})
    if is_ml:
        return deals, encoding_dict
    return deals


def construction_stage(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Кодирует столбец «Стадия строительной готовности на дату договора». Целыми числами по логической стадии
    завершенности.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Стадия строительной готовности на дату договора».
    """
    deals = deals.copy()
    encoding_dict = {
        'Введен в эксплуатацию': 0,
        'Монтажные и отделочные работы': 1,
        'Начало монтажных работ': 2,
        'Работы нулевого цикла': 3,
        'Получение РВЭ, благоустройство территории': 4,
        'Строительство не начато': 5,
        'На дату договора активности по проекту не фиксировалось': 6
    }
    deals['Стадия строительной готовности на дату договора'] = deals[
        'Стадия строительной готовности на дату договора'].map(encoding_dict)
    return deals


def price_per_square_meter(deals: pd.DataFrame, column_name: str = 'Цена за кв. метр',
                           nan_replacement: float = 0.0) -> pd.DataFrame:
    """
    Кодирует признак 'Цена за кв. метр' следующим образом:
    Nan -> nan_replacement
    Преобразование значений во float

    :param deals: Данные о сделках.
    :param column_name:
    :param nan_replacement:
    :return: Копия сделок с преобразованным признаком «Цена за кв. метр»
    """
    deals = deals.copy()
    for i, val in deals[column_name].isna().items():
        if val:
            deals.at[i, column_name] = nan_replacement
        else:
            try:
                deals.at[i, column_name] = float(deals.at[i, column_name].replace(',', '.'))
            except AttributeError:
                deals.at[i, column_name] = float(deals.at[i, column_name])
    deals = deals.astype({column_name: float})
    return deals


def discounts_by_contract_date(deals: pd.DataFrame, column_name='Скидки по дате договора',
                               value_for_false=None) -> pd.DataFrame:
    """
    Кодирует категориальный признак 'Скидки по дате договора' следующим образом:
    NaN -> 0
    Скидок нет, Скидки не предоставляются, Скидка не предоставляется -> 0
    Есть скидки -> 1

    :param deals: Данные о сделках.
    :param column_name:
    :param value_for_false:
    :return: Копия сделок с преобразованным признаком «Скидки по дате договора»
    """
    if value_for_false is None:
        value_for_false = ['Скидок нет', 'Скидки не предоставляются',
                           'Скидка не предоставляется', 'Без скидки']

    deals = deals.copy()
    for i, val in deals[column_name].isna().items():
        if val:
            deals.at[i, column_name] = 0
        else:
            if deals.at[i, column_name] in value_for_false:
                deals.at[i, column_name] = 0
            else:
                deals.at[i, column_name] = 1
    deals = deals.astype({column_name: int})
    return deals


def body_finishing(deals: pd.DataFrame, column_name='Отделка по корпусу',
                   value_for_zero=None, value_for_one=None,
                   value_for_two=None) -> pd.DataFrame:
    """
    Кодирует категориальный признак 'Отделка по корпусу' следующим образом:
    NaN -> 0
    Без отделки -> 0
    Под чистовую -> 1
    Есть отделка -> 2

    :param deals: Данные о сделках.
    :param column_name:
    :param value_for_zero:
    :param value_for_one:
    :param value_for_two:
    :return: Копия сделок с преобразованным признаком «Отделка по корпусу»
    """
    if value_for_zero is None:
        value_for_zero = ['Без отделки']

    if value_for_one is None:
        value_for_one = ['Под чистовую']

    if value_for_two is None:
        value_for_two = ['С отделкой', 'С отделкой и без', 'Под чистовую и с отделкой']

    deals = deals.copy()
    for i, val in deals[column_name].isna().items():
        if val:
            deals.at[i, column_name] = 0
        else:
            if deals.at[i, column_name] in value_for_zero:
                deals.at[i, column_name] = 0
            elif deals.at[i, column_name] in value_for_one:
                deals.at[i, column_name] = 1
            elif deals.at[i, column_name] in value_for_two:
                deals.at[i, column_name] = 2
            else:
                deals.at[i, column_name] = 0
    deals = deals.astype({column_name: int})
    return deals


def wholesale_transaction(deals: pd.DataFrame, column_name='Участие объекта в оптовой сделке',
                          value_for_true='ДА') -> pd.DataFrame:
    """

    Кодирует признак бинарный признак 'Участие объекта в оптовой сделке' следующим образом:
    ДА -> 1
    НЕТ -> 0

    :param deals: Данные о сделках.
    :param column_name:
    :param value_for_true:
    :return: Копия сделок с преобразованным признаком «Участие объекта в оптовой сделке»
    """
    deals = deals.copy()
    deals[column_name] = (deals[column_name] == value_for_true).astype(np.uint8)
    return deals


def drop_columns(deals: pd.DataFrame,
                 column_names: tp.Optional[list[str]] = None) -> pd.DataFrame:
    """
    Удаляет выбранные признаки из сделок

    :param deals: Данные о сделках.
    :param column_names: Имена оставляемых столбцов.
    :return: Копия сделок с удалёнными столбцами.
    """
    if column_names is None:
        column_names = ["Проект", "ID корпуса", "Стадия строительной готовности на дату договора",
                        "Район", "Локация", "Заявленный срок ввода в эксплуатацию", "Старт продаж",
                        "Класс", "Девелопер", "Застройщик", "Дата договора", "Тип сделки",
                        "Тип объекта", "Этаж", "Количество комнат", "Площадь согласно ПД",
                        "Цена за кв. метр", "Скидки по дате договора", "Отделка по корпусу",
                        "Участие объекта в оптовой сделке", "latitude", "longitude"]

    deals = deals.copy()
    return deals[column_names]


def developer(data: pd.DataFrame,
              save_old: bool = True) -> pd.DataFrame:
    """
    Конвертирует признак «Девелопер» в int32, нумеруя их по количеству сделок, где 1 соответствует наибольшему
    значению.\n
    :param data: Данные о сделках.
    :param save_old: сохранять ли первоначальный столбец
    :return: Копия сделок с преобразованным признаком «Девелопер».
    """
    vc = data["Девелопер"].value_counts().to_dict()
    for id1, val in enumerate(vc):
        vc[val] = id1 + 1
    df = data.copy()
    if save_old:
        df["developer_old"] = df["Девелопер"]
    df["Девелопер"] = df["Девелопер"].map(vc)
    return df


def builder(data: pd.DataFrame,
            save_old: bool = True) -> pd.DataFrame:
    """
    Конвертирует признак «Застройщик» в int32, нумеруя их по количеству сделок, где 1 соответствует наибольшему
    значению.

    :param data: Данные о сделках.
    :param save_old: Оставлять ли необработанные данные.
    :return: Копия сделок с преобразованным признаком «Застройщик».
    """
    vc = data["Застройщик"].value_counts().to_dict()
    for id1, val in enumerate(vc):
        vc[val] = id1 + 1
    df = data.copy()
    if save_old:
        df["builder_old"] = df["Застройщик"]
    df["Застройщик"] = df["Застройщик"].map(vc)
    return df


def area(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Конвертирует признак «Площадь согласно ПД» в float.

    :param deals: Данные о сделках.
    :return: Копия сделок с преобразованным признаком «Площадь согласно ПД» 
    """
    df = deals.copy()
    try:
        df["Площадь согласно ПД"] = pd.to_numeric(deals['Площадь согласно ПД'].str.replace(',', '.'), errors='coerce')
    except ValueError:
        print("Проблемы с площадью")
    except AttributeError:
        pass
    return df


def class_(deals: pd.DataFrame, class_mapping=None) -> pd.DataFrame:
    """
    Конвертирует признак «Класс» в int8, ставя каждому классу в соответствие его "элитность" (1 - самый элитный)\n

    :param deals: Данные о сделках.
    :param class_mapping: словарь для кодировки районов.
    :return: Копия сделок с преобразованным признаком «Класс».
    """
    df = deals.copy()
    df["Класс"] = df["Класс"].map(class_mapping)
    return df


def add_days_after_start(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет признак: количество дней после начала продаж.

    :param deals: Данные о сделках с англоязычными признаками.
    :return: Копия сделок c новым признаком `days_after_start`
    """
    df = deals.copy()
    df["days_after_start"] = df["time_after_start"].dt.days
    return df


def add_days_before_completeness(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет новый столбец 'days_before_completeness' в DataFrame, содержащий количество дней
    до окончания строительства

    :param deals:Данные о сделках с англоязычными признаками.
    :return: Копия сделок с новым столбцом 'days_before_completeness'.
    """
    df = deals.copy()
    df["days_before_completeness"] = df["time_before_completeness"].dt.days
    return df


def calculate_room_area(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Рассчитывает среднюю площадь на одну комнату.

    :param deals: Данные о сделках с англоязычными признаками.
    :return Копия сделок с новым столбцом 'room_area'.
    """
    df = deals.copy()
    df["room_area"] = df["area"] / (1 + df["rooms_number"])
    return df


def add_year_month_day(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Создает новый столбец 'year_month_day' в DataFrame, который содержит дату сделки в числовом формате YYYYMMDD.

    :param deals: Данные о сделках с англоязычными признаками.
    :return: Копия сделок с новым столбцом 'year_month_day'.
    """
    df = deals.copy()
    df["year_month_day"] = (deals.contract_date.dt.year * 10000 +
                            deals.contract_date.dt.month * 100 +
                            deals.contract_date.dt.day)
    return df


def start_of_sales(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Создает новый признак «Время после старта» в формате timedelta64, заполняя значениями:
    data["Дата договора"] - data["Старт продаж"]

    :param deals: Данные о сделках.
    :return: Копия сделок с удаленным признаком «Старт продаж» и новым признаком "Время после старта".
    """
    df = deals.copy()
    df = df.dropna(subset=['Старт продаж'])
    df["Дата договора"] = pd.to_datetime(df["Дата договора"])
    df["Старт продаж"] = pd.to_datetime(df["Старт продаж"])
    df["Время после старта"] = df["Дата договора"] - df["Старт продаж"]
    # df = df.drop(["Старт продаж"], axis=1)
    return df


def date_of_exploitation(deals: pd.DataFrame, quantile_level: tp.Optional[float] = 0.5) -> pd.DataFrame:
    """
    Создает новый признак «Время до ввода» в формате timedelta64, заполняя значениями:
    data["Заявленный срок ввода в эксплуатацию"] - data["Дата договора"]

    :param deals: Данные о сделках.
    :param quantile_level: Уровень квантили для заявленного срока ввода в эксплуатацию.
    :return: Копия сделок с удаленным признаком «Заявленный срок ввода в эксплуатацию» и новым признаком
    "Время до ввода".
    """
    df = deals.copy()
    df = drop_nan(df, quantile_level=quantile_level)
    df["Время до ввода"] = pd.to_datetime(df["Заявленный срок ввода в эксплуатацию"]) - df["Дата договора"]
    df = df.drop(["Заявленный срок ввода в эксплуатацию", "Старт продаж"], axis=1)
    return df


def copy_old_columns(deals: pd.DataFrame, columns_names: list[str], suffix: str = "_old") -> pd.DataFrame:
    """
    Копирует указанные столбцов с добавлением заданного суффикса к их названиям.

    :param deals: Данные о сделках.
    :param columns_names: Список названий столбцов на английском языке, которые нужно скопировать.
    :param suffix: Суффикс, который будет добавлен к названиям копируемых столбцов.
    :return: Копия сделок с добавленными копиями указанных столбцов.
    """
    deals_copy = deals.copy()

    for column_name in columns_names:
        if column_name in deals_copy.columns:
            deals_copy[f"{column_name}{suffix}"] = deals_copy[column_name]
        else:
            print(f"Warning: Column '{column_name}' does not exist in DataFrame.")
    return deals_copy


def rename_columns(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Переименовывает столбцы DataFrame согласно заданному маппингу.

    :param deals: Данные о сделках
    :return: Копия сделок с переименованными столбцами.
    """
    names = {
        "ID корпуса": "house_id",
        "Проект": "project",
        "Локация": "location",
        "Район": "district",
        "Стадия строительной готовности на дату договора": "stage",
        "Заявленный срок ввода в эксплуатацию": "time_to_completion",
        "Старт продаж": "start_sales",
        "Класс": "class",
        "Девелопер": "developer",
        "Застройщик": "builder",
        "Дата договора": "contract_date",
        "Тип сделки": "deal_type",
        "Этаж": "floor",
        "Количество комнат": "rooms_number",
        "Площадь согласно ПД": "area",
        "Цена за кв. метр": "price",
        "Скидки по дате договора": "promotions",
        "Отделка по корпусу": "finish",
        "Участие объекта в оптовой сделке": "wholesale_deal",
        "Кладовые": "pantry",
        "Паркинг": "parking",
        "Время после старта": "time_after_start",
        "Время до ввода": "time_before_completeness"
    }
    deals_renamed = deals.rename(columns=names)
    return deals_renamed
