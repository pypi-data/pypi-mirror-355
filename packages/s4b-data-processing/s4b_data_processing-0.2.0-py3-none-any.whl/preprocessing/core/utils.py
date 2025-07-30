import re

import numpy as np
import pandas as pd


def relative_number_type(types: pd.Series, type1: str, type2: str) -> float:
    """
    Функция подсчитывает количество раз, которое встречается каждый из двух указанных типов,
    и возвращает отношение количества первого типа к количеству второго. Если второй тип не
    встречается ни разу, функция возвращает NaN, чтобы избежать деления на ноль.


    :param types: pd.Series, содержащий категориальные данные, в которых осуществляется подсчёт.
    :param type1: Название первого типа для подсчёта.
    :param type2: Название второго типа для подсчёта и вычисления относительного количества по отношению к первому типу.
    :return:
    """
    number_type1 = np.sum((types == type1))
    number_type2 = np.sum((types == type2))
    if number_type2 != 0:
        return number_type1 / number_type2

    return np.nan


def remove_price_outliers(deals: pd.DataFrame, alpha: float = 0.005) -> pd.DataFrame:
    """
    Удаляет выбросы по цене, используя квантили.

    :param deals: Данные со сделками.
    :param alpha: Процент сделок выбрасываемых при фильтрации.
    :return: Сделки без выбросов.

    """
    q_left = deals["price"].quantile(alpha / 2)
    q_right = deals["price"].quantile(1 - alpha / 2)
    quantile_mask = (q_left <= deals["price"]) & (deals["price"] <= q_right)
    deals_filtered = deals[quantile_mask]
    return deals_filtered


def get_interest_rate(deals: pd.DataFrame, target_name: str = "price", is_ml: bool = True) -> pd.Series:
    """
    Функция позволяет оценить скорость изменения параметра target_name.

    :param deals: Данные со сделками.
    :param target_name: параметр, для которого оцениваем скорость изменения.
    :param is_ml: параметр, отвечающий за способ дисконтирования. True -- ретроспективно,
    False -- по актуальным данным.
    :return: временной ряд, соответствующий скорости изменения target
    """
    deals = deals.copy()
    deals["contract_date"] = pd.to_datetime(deals["contract_date"])
    deals = deals[deals[target_name] != 0]
    pct = (1 + deals.set_index("contract_date")[target_name]
           .resample("ME")
           .mean()
           .to_period("M")
           .pct_change(fill_method="ffill"))
    if is_ml:
        pct = pct.shift()
    return pct.fillna(1).cumprod()

def discounting(deals: pd.DataFrame, interest_rate: pd.Series, target_name: str = "price", to_today: bool = True) -> pd.Series:
    """
    Функция возвращает ряд с приведёнными ценами (дисконтирование назад или актуализация вперёд).

    :param deals: Данные со сделками.
    :param interest_rate: временной ряд, соответствующий скорости изменения параметра target
    :param target_name: изучаемый параметр.
    :param to_today: Приводить ли цены к последнему месяцу interest_rate (True) или дисконтировать к базе (False, по умолчанию).
    :return: ряд с дисконтированными ценами.
    Цены, равные 0, остаются без изменений и не влияют на расчёт коэффициентов.
    """
    if to_today:
        if len(interest_rate) >= 2:
            target_factor = interest_rate.iloc[-2]
        else:
            target_factor = interest_rate.iloc[-1]
        last_period = interest_rate.index[-1]
    else:
        target_factor = None
        last_period = None

    def _apply(grp):
        period = grp.name.to_period("M")
        rate = interest_rate.get(period, 1)
        if rate == 0:
            return grp
        if to_today and period == last_period:
            return grp
        mask = grp != 0
        out = grp.copy()
        if to_today:
            out[mask] = grp[mask] * (target_factor / rate)
        else:
            out[mask] = grp[mask] / rate
        return out

    return (
        deals.set_index("contract_date", append=True)[target_name]
             .resample("ME", level=1)
             .transform(_apply)
             .reset_index(level=1, drop=True)
    )
    

def add_discounting_price(
        deals: pd.DataFrame,
        target_name: str = "price",
        is_ml: bool = False,
        to_today: bool = True,
        col_name: str = "price_disc"
) -> pd.DataFrame:

    df = deals.copy()
    ir = get_interest_rate(df, target_name=target_name, is_ml=is_ml)
    df[col_name] = discounting(df, ir, target_name=target_name, to_today=to_today)
    return df


def compounding(deals: pd.DataFrame, interest_rate: pd.Series, target_name: str = "price") -> pd.Series:
    """
    Функция возвращает ряд с компаундированными ценами (процедура, обратная дисконтированию).

    :param deals: Данные со сделками.
    :param interest_rate: временной ряд, соответствующий скорости изменения параметра target
    :param target_name: изучаемый параметр.
    :return: ряд с компаундированными ценами
    """
    return (deals.set_index("contract_date", append=True)[target_name]
            .resample("M", level=1)
            .transform(lambda x: x * interest_rate[x.name.to_period("M")])
            .reset_index(level=1, drop=True))


def uniform_distribute_geo(deals: pd.DataFrame, r: float):
    """
    Равномерно распределяет геоточки вокруг геоточки проекта с радиусом r

    :param deals: Данные со сделками.
    :param r: Радиус(км)
    :return: Новый набор данных с равномерно распределенными геоточками
    """
    deals = deals.copy()
    r = 1 / 111 * r
    angle = np.random.uniform(0, 2 * np.pi, len(deals["latitude"]))
    radius = np.sqrt(np.random.uniform(0, r ** 2, len(deals["longitude"])))
    deals["latitude"] = deals["latitude"] + radius * np.sin(angle)
    deals["longitude"] = deals["longitude"] + radius * np.cos(angle)
    return deals


def clean_string_columns(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Преобразует все строковые колонки в DataFrame, приводя их к нижнему регистру
    и обрезая пробелы слева и справа.

    :param deals: Данные со сделками.
    :return: Новый набор данных с преобразованными строковыми колонками.
    """
    deals = deals.copy()
    string_columns = deals.select_dtypes(include=['object']).columns

    # for col in string_columns:
    #     deals[col] = deals[col].str.lower().str.strip(
    for col in string_columns:
        deals[col] = deals[col].apply(lambda x: x.lower().strip() if isinstance(x, str) else x)
    return deals

