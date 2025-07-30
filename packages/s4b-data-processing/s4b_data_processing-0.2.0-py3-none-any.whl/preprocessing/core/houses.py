import pandas as pd

from . import features
from . import utils


def compute_corpus_stats(df_deals: pd.DataFrame, df_pd: pd.DataFrame) -> pd.DataFrame:
    flags = df_pd.assign(
        is_apartment=(df_pd["Тип объекта недвижимости"] == "квартира").astype(int),
        is_pantry=(df_pd["Тип объекта недвижимости"] == "кладовка").astype(int),
        is_parking=(df_pd["Тип объекта недвижимости"] == "машино-место").astype(int),
    )

    flags["Этаж"] = pd.to_numeric(flags["Этаж"], errors="coerce")

    agg = (
        flags
        .groupby("ID корпуса")
        .agg(
            total_apartment=("is_apartment", "sum"),
            pantry_count=("is_pantry", "sum"),
            parking_count=("is_parking", "sum"),
            max_floor=("Этаж", "max"),
        )
        .reset_index()
    )

    agg = agg[agg["total_apartment"] > 0].copy()
    agg["pantry"] = agg["pantry_count"] / agg["total_apartment"]
    agg["parking"] = agg["parking_count"] / agg["total_apartment"]
    agg = agg[["ID корпуса", "total_apartment", "pantry", "parking", "max_floor"]]

    result = df_deals[df_deals["ID корпуса"].isin(agg["ID корпуса"])].copy()
    agg_indexed = agg.set_index("ID корпуса")

    result["total_apartment"] = result["ID корпуса"].map(agg_indexed["total_apartment"])
    result["pantry"] = result["ID корпуса"].map(agg_indexed["pantry"])
    result["parking"] = result["ID корпуса"].map(agg_indexed["parking"])
    result["Этаж"] = result["ID корпуса"].map(agg_indexed["max_floor"])

    return result


def preprocess_houses(df_deals: pd.DataFrame, df_pd: pd.DataFrame) -> pd.DataFrame:
    df_stats = compute_corpus_stats(df_deals, df_pd)

    df_prepared = (
        df_stats
        .pipe(features.price_per_square_meter)
        .pipe(features.contract_date)
        .pipe(features.area)
        .pipe(features.number_rooms)
        .pipe(features.start_of_sales)
        .pipe(features.floor)
        .pipe(features.rename_columns)
        .pipe(features.add_days_after_start)
        .pipe(utils.clean_string_columns)
        .pipe(utils.add_discounting_price)
        .pipe(utils.remove_price_outliers)
    )

    grouped_pd = df_pd.groupby("ID корпуса")

    def house_description(group: pd.DataFrame) -> dict:
        project, house_id = group.name

        pd_group = grouped_pd.get_group(house_id).copy()
        pd_group = pd_group[pd_group["Кол-во комнат"] != "Без типа"]

        pd_group["Кол-во комнат"] = (
            pd_group["Кол-во комнат"].replace("ст", 0).pipe(lambda s: pd.to_numeric(s, errors="coerce"))
        )

        pd_group["Кол-во комнат"] = pd_group["Кол-во комнат"].fillna(-1).astype(int)

        pd_group["rooms_cat"] = pd_group["Кол-во комнат"].apply(
            lambda x: x if 0 <= x < 5 else (5 if x >= 5 else -1)
        )

        group = group.copy()
        group["rooms_cat"] = group["rooms_number"].apply(
            lambda x: x if (pd.notna(x) and 0 <= x < 5) else (5 if (pd.notna(x) and x >= 5) else -1)
        )

        description_dict: dict = {"project": project, "house_id": house_id}

        freq = (
            pd_group.loc[pd_group["rooms_cat"] != -1, "rooms_cat"]
            .value_counts(normalize=True)
            .reindex([0, 1, 2, 3, 4, 5], fill_value=0)
            .sort_index()
        )
        description_dict |= {f"rooms_{i}": freq.loc[i] for i in freq.index}

        description_dict["rooms_number_mean"] = pd_group.loc[pd_group["Кол-во комнат"] >= 0, "Кол-во комнат"].mean()

        start_sales_quantile = group["contract_date"].quantile(0.05)
        if not pd.isna(start_sales_quantile):
            description_dict["start_year_sales"] = start_sales_quantile.year
            description_dict["start_sales"] = start_sales_quantile

        description_dict["deals_sold"] = min(len(group) / group["total_apartment"].mean(), 1)
        description_dict["ndeals"] = group["total_apartment"].mean()

        description_dict["mean_area"] = pd_group["Общая проектная площадь с НЛП"].mean()

        nonzero_prices = group.loc[group["price"] > 0, "price"]
        description_dict["mean_price_orig"] = nonzero_prices.mean() if not nonzero_prices.empty else pd.NA

        nonzero_disc = group.loc[group["discounting_price"] > 0, "discounting_price"]
        description_dict["mean_price"] = nonzero_disc.mean() if not nonzero_disc.empty else pd.NA
        group["days_after_start"] = (group["contract_date"] - start_sales_quantile).dt.days
        filtered_group = group
        if not filtered_group.empty:
            description_dict["mean_selling_time"] = filtered_group["days_after_start"].mean()
        desc_prices = (
            group
            .loc[(group["discounting_price"] > 0) & (group["rooms_cat"] != -1)]
            .groupby(group["rooms_cat"].astype(int))["discounting_price"]
            .mean()
            .reindex([0, 1, 2, 3, 4, 5], fill_value=0)
            .sort_index()
            .add_suffix("_mean_price")
            .to_dict()
        )
        description_dict |= desc_prices
        area_by_rooms = (
            pd_group
            .loc[pd_group["rooms_cat"] != -1]
            .groupby(pd_group["rooms_cat"].astype(int))["Общая проектная площадь с НЛП"]
            .mean()
            .reindex([0, 1, 2, 3, 4, 5], fill_value=0)
            .sort_index()
            .add_suffix("_mean_area")
            .to_dict()
        )
        description_dict |= area_by_rooms
        time_by_rooms = (
            group
            .loc[group["rooms_cat"] != -1]
            .groupby(group["rooms_cat"].astype(int))["days_after_start"]
            .mean()
            .reindex([0, 1, 2, 3, 4, 5], fill_value=0)
            .sort_index()
            .add_suffix("_mean_selling_time")
            .to_dict()
        )
        description_dict |= time_by_rooms
        description_dict["mean_selling_time"] = filtered_group["days_after_start"].mean()
        description_dict["median_selling_time"] = filtered_group["days_after_start"].median()
        description_dict["q90_selling_time"] = filtered_group["days_after_start"].quantile(0.90)

        valid = pd_group.loc[pd_group["Кол-во комнат"] >= 0].copy()
        description_dict["mean_room_area"] = (
            (valid["Общая проектная площадь с НЛП"] / (1 + valid["Кол-во комнат"]))
            .mean()
        )
        cls_mode = group["class"].dropna().mode()
        description_dict["class"] = cls_mode.iloc[0] if not cls_mode.empty else None

        description_dict["latitude"] = group["latitude"].mean()
        description_dict["longitude"] = group["longitude"].mean()
        description_dict["pantry"] = group["pantry"].mean()
        description_dict["parking"] = group["parking"].mean()
        description_dict["floor"] = group["floor"].mean()

        dev_mode = group["developer"].dropna().mode()
        description_dict["developer"] = dev_mode.iloc[0] if not dev_mode.empty else None

        return description_dict

    df_houses_layouts = pd.json_normalize(
        df_prepared
        .groupby(["project", "house_id"])
        .apply(house_description)
        .rename("agg")
    )

    return df_houses_layouts
