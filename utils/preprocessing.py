import json
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures

CURRENT_YEAR = 2025


def read_json_stat(file_path: str) -> pd.DataFrame:
    """
    Read a JSON-stat file as an input and return a parsed Dataframe
    """
    with open(file_path, encoding="utf-8") as input_file:
        data = json.load(input_file)

    # Extracting the dimensions and values
    dimensions = data["dataset"]["dimension"]
    values = data["dataset"]["value"]

    # Creating a list of headers for the DataFrame
    headers = [dimensions[dim]["label"] for dim in dimensions["id"]] + ["Value"]

    # Creating a list of rows for the DataFrame
    rows = []
    for i, value in enumerate(values):
        row = []
        for dim in dimensions["id"]:
            for key, index in dimensions[dim]["category"]["index"].items():
                if index == i % dimensions["size"][dimensions["id"].index(dim)]:
                    row.append(dimensions[dim]["category"]["label"][key])
        row.append(value)
        rows.append(row)

    # Creating the DataFrame
    df = pd.DataFrame(rows, columns=headers)

    return df


def transform_mileage(df_col: pd.Series) -> pd.Series:
    df = df_col.to_frame()
    df["mileage"] = df.iloc[:, 0]
    df["mileage_log"] = np.log(df["mileage"])
    return df["mileage_log"]


def transform_model(df_col: pd.Series) -> pd.Series:
    # Get reference value
    MODEL_REF_PRICE_PATH = "data/model_ref_price_full.csv"
    MODEL_REF_EXTRA_PRICE_PATH = "data/model_ref_price_extra.csv"
    df_variants = pd.read_csv(MODEL_REF_PRICE_PATH)
    df_model_extra = pd.read_csv(MODEL_REF_EXTRA_PRICE_PATH)
    # df_model_ref_price["ref_price_clean"] = pd.to_numeric(
    #     df_model_ref_price["ref_price"].str.replace(".", "")
    # )

    # Filter out null price
    df_variants.dropna(subset="price_min", inplace=True)

    # Get mean price
    df_variants["price_avg"] = (df_variants["price_min"] + df_variants["price_max"]) / 2

    # Get model. Resolve case with 'Air Blade'
    df_variants["model_original"] = (
        df_variants["model_name"].str.split().apply(lambda x: x[0])
    )
    df_variants["model"] = df_variants["model_original"].case_when(
        caselist=[
            (df_variants["model_name"].str.contains("Air Blade"), "Air Blade"),
            (df_variants["model_name"].str.contains("SH Mode"), "SH Mode"),
            (df_variants["model_name"].str.contains("Super Cub"), "Cub"),
            (df_variants["model_name"].str.contains("Winner X"), "Winner X"),
            (df_variants["brand_name"].eq("Vespa"), "Vespa"),
        ]
    )

    # Get average price by model
    df_model_ref_price_original = df_variants.groupby(by="model", as_index=False).agg(
        {"price_avg": "mean"}
    )
    df_model_ref_price = pd.concat([df_model_ref_price_original, df_model_extra])
    df_model_ref_price["price_avg_log"] = np.log(
        df_model_ref_price["price_avg"] * 1_000
    )

    # Join with dataframe
    df = df_col.to_frame()
    df["model"] = df.iloc[:, 0]

    # # Check join
    # # Get unique input models
    # df_input_distinct_models = pd.DataFrame(df["model"].unique())
    # df_input_distinct_models["model"] = df_input_distinct_models.iloc[:, 0]
    # # Join against ref models
    # df_merge = df_input_distinct_models.merge(
    #     right=df_model_ref_price, left_on="model", right_on="model", how="left"
    # )
    # # Check not joined values
    # not_joined_list = sorted(df_merge[df_merge["price_avg"].isnull()]["model"].unique())

    # # Check what model in top 20 doesn't have ref price, filter out 'Dòng khác'
    # df_filter = df[~df["model"].isin(["Dòng khác", "dòng khác"])]
    # df_model_count = (
    #     df_filter.groupby("model").agg(counts=("model", "count")).reset_index()
    # )
    # df_input_top_20 = df_model_count.sort_values(by="counts", ascending=False).head(20)
    # top_20_not_in_list = df_input_top_20[df_input_top_20["model"].isin(not_joined_list)]

    # # Check if value is in full list
    # df_variants[df_variants["model_name"].str.contains("blade", case=False)]

    output_df = df.merge(
        right=df_model_ref_price, left_on="model", right_on="model", how="left"
    )

    # # Check for nan values
    # count_nan_value = int(output_df["ref_price_clean_log"].isnull().sum())
    # if count_nan_value > 0:
    #     logging.error(
    #         f"There are nan values: {output_df[output_df['ref_price_clean_log'].isnull()]}"
    #     )
    #     raise ValueError(f"Found {count_nan_value} nan values")

    return output_df["price_avg_log"]


def transform_origin(df_col: pd.Series) -> pd.Series:
    # Get reference value
    COUNTRY_MULTIPLIER_PATH = "data/origin_country_multiplier.csv"
    df_countries = pd.read_csv(COUNTRY_MULTIPLIER_PATH)

    # Join with dataframe
    df = df_col.to_frame()
    df["origin"] = df.iloc[:, 0]
    output_df = df.merge(
        right=df_countries, left_on="origin", right_on="country_name", how="left"
    )

    # Check for nan values
    count_nan_value = int(output_df["country_multiplier"].isnull().sum())
    if count_nan_value > 0:
        logging.error(
            f"There are nan values: {output_df[output_df['country_multiplier'].isnull()]}"
        )
        raise ValueError(f"Found {count_nan_value} nan values")

    return output_df["country_multiplier"]


def transform_province(df_col: pd.Series) -> pd.Series:
    """
    Note that the input here must be picked from the input_scoli itself,
    otherwise join will introduce nan values
    """
    # Get reference value
    SCOLI_PATH = "data/input_scoli_2023.json"
    df_scoli = read_json_stat(file_path=SCOLI_PATH)
    df_scoli.columns = ["province", "year", "province_scoli"]

    # Join with dataframe
    df = df_col.to_frame()
    df["province"] = df.iloc[:, 0]
    output_df = df.merge(
        right=df_scoli, left_on="province", right_on="province", how="left"
    )

    # Check for nan values
    count_nan_value = int(output_df["province_scoli"].isnull().sum())
    if count_nan_value > 0:
        logging.error(
            f"There are nan values: {output_df[output_df['province_scoli'].isnull()]}"
        )
        raise ValueError(f"Found {count_nan_value} nan values")

    return output_df["province_scoli"]


def transform_reg_year(df_col: pd.Series) -> pd.Series:
    # Read column
    df = df_col.to_frame()
    df["reg_year"] = df.iloc[:, 0]
    df["age"] = CURRENT_YEAR - df["reg_year"]

    # Move age = 0 to age = 0.5 since the bike must have some age
    df["age_updated"] = df["age"].case_when(caselist=[(df["age"].eq(0), 0.5)])

    df["age_log"] = np.log(df["age_updated"])

    return df["age_log"]


def transform_prediction_input(input: dict) -> np.ndarray:
    """
    Transform inputs from user and output as the model input
    Input should have these fields:
    - mileage
    - model
    - origin
    - province
    - reg_year
    """
    df = pd.DataFrame(input)
    df["age_log"] = transform_reg_year(df_col=df["reg_year"])
    df["mileage_log"] = transform_mileage(df_col=df["mileage"])
    df["origin_multiplier"] = transform_origin(df_col=df["origin"])
    df["model_ref_price_log"] = transform_model(df_col=df["model"])
    df["province_scoli"] = transform_province(df_col=df["province"])

    # Polynomial for age_log with intercept
    poly = PolynomialFeatures(degree=3)
    age_log_poly_intercept = poly.fit_transform(df[["age_log"]])

    # Polynomial regression with mileage
    X = np.hstack(
        (
            age_log_poly_intercept,
            df[
                [
                    "mileage_log",
                    "origin_multiplier",
                    "model_ref_price_log",
                    # "province_scoli",
                ]
            ],
        )
    )

    return X


def mean_absolute_percentage_error(y_true, y_pred, axis: int = None):
    """
    Ref:
    - https://stackoverflow.com/questions/55996319/my-mape-mean-absolute-percentage-error-function-returns-a-number-over-100-when
    - https://www.statsmodels.org/dev/_modules/statsmodels/tools/eval_measures.html#meanabs

    Returns: percentage without multiplying with 100
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true), axis=axis)
