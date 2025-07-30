from .features import *
from .utils import uniform_distribute_geo, remove_price_outliers, clean_string_columns, get_interest_rate, add_discounting_price
from preprocessing import CITIES_SETTINGS

import sys
import os


def preprocessing(deals: pd.DataFrame,
                  nan_replacement: tp.Optional[float] = None,
                  is_ml=False,
                  keep_original_columns=False,
                  remove_outliers=True,
                  distribute_r=0,
                  city_name="nsk") -> pd.DataFrame:
    """
    Функция для выполнения первоначальной предобработки набора данных со сделками.

    :param deals: Исходный DataFrame с информацией о сделках.
    :param nan_replacement: Значение для замены NaN в данных о цене за квадратный метр.
    :param is_ml: Если False,то происходит кодирование районов по убывающей средней цене по всему DataFrame.
    :param keep_original_columns: Сохранять ли исходные столбцы в результате.
    :param remove_outliers: Удалять ли выбросы по цене.
    :param distribute_r: Радиус для распределения значений.
    :param city_name: Название города, для которого применяются настройки предобработки.
    :return: Предобработанный DataFrame со сделками.
    """
    city_settings = CITIES_SETTINGS[city_name]
    class_mapping = city_settings["class_mapping"]

    def pipeline(df):
        return (df
                .pipe(drop_columns if not keep_original_columns else lambda x: x)
                .pipe(uniform_distribute_geo, r=distribute_r)
                .pipe(estate_type)
                .pipe(price_per_square_meter, nan_replacement=nan_replacement)
                .pipe(contract_date)
                .pipe(project)
                .pipe(area)
                .pipe(deal_type)
                .pipe(location)
                .pipe(construction_stage)
                .pipe(discounts_by_contract_date)
                .pipe(wholesale_transaction)
                .pipe(body_finishing)
                .pipe(class_, class_mapping)
                .pipe(developer)
                .pipe(builder)
                .pipe(district if not is_ml else lambda x: x)
                .pipe(floor)
                .pipe(number_rooms)
                .pipe(start_of_sales)
                .pipe(date_of_exploitation)
                .pipe(corpus_id)
                .pipe(rename_columns)
                .pipe(add_days_after_start)
                .pipe(add_days_before_completeness)
                .pipe(calculate_room_area)
                .pipe(add_year_month_day)
                .pipe(clean_string_columns)
                .pipe(add_discounting_price)
                .pipe(remove_price_outliers if remove_outliers else lambda x: x))

    return pipeline(deals.copy())
