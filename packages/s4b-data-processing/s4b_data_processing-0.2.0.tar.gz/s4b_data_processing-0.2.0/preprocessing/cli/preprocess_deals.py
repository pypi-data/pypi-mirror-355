import argparse
import pandas as pd
from pathlib import Path

from preprocessing.core.preprocessing import preprocessing
import warnings

warnings.filterwarnings("ignore")


def load_dataframe(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    elif path.suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    if path.suffix == ".parquet":
        df.to_parquet(path, index=False)
    elif path.suffix in {".xlsx", ".xls"}:
        df.to_excel(path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def main(args=None) -> None:
    parser = argparse.ArgumentParser(description="Preprocess real estate deals dataset")
    parser.add_argument("input", type=Path, help="Path to input parquet/xlsx file")
    parser.add_argument("output", type=Path, help="Path to save processed file")
    parser.add_argument("city", help="City code used for preprocessing")
    parser.add_argument("--nan-replacement", type=float, default=None,
                        help="Replacement for NaN price per sq meter")
    parser.add_argument("--ml", action="store_true", default=False, help="Use ML preprocessing variant")
    parser.add_argument("--keep-original", action="store_true", default=False, help="Keep original columns")
    parser.add_argument("--no-outliers", action="store_true", default=False, help="Do not remove price outliers")
    parser.add_argument("--distribute-r", type=float, default=0.0,
                        help="Radius in km for uniform distribution of geolocations")

    parsed = parser.parse_args(args)

    df = load_dataframe(parsed.input)
    processed = preprocessing(
        deals=df,
        nan_replacement=parsed.nan_replacement,
        is_ml=parsed.ml,
        keep_original_columns=parsed.keep_original,
        remove_outliers=not parsed.no_outliers,
        distribute_r=parsed.distribute_r,
        city_name=parsed.city,
    )

    processed = processed.sort_values(by="contract_date").reset_index(drop=True)
    save_dataframe(processed, parsed.output)


if __name__ == "__main__":
    main()
