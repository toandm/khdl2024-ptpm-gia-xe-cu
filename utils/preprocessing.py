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
    MODEL_REF_PRICE_PATH = "data/model_ref_price.csv"
    df_model_ref_price = pd.read_csv(MODEL_REF_PRICE_PATH)
    df_model_ref_price["ref_price_clean"] = pd.to_numeric(
        df_model_ref_price["ref_price"].str.replace(".", "")
    )

    # Join with dataframe
    df = df_col.to_frame()
    df["model"] = df.iloc[:, 0]
    output_df = df.merge(
        right=df_model_ref_price, left_on="model", right_on="model", how="left"
    )

    output_df["ref_price_clean_transform"] = np.log(
        output_df["ref_price_clean"] / 1_000
    )

    # Check for nan values
    count_nan_value = int(output_df["ref_price_clean_transform"].isnull().sum())
    if count_nan_value > 0:
        logging.error(
            f"There are nan values: {output_df[output_df['ref_price_clean_transform'].isnull()]}"
        )
        raise ValueError(f"Found {count_nan_value} nan values")

    return output_df["ref_price_clean_transform"]


def transform_origin(df_col: pd.Series) -> pd.Series:
    pass


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
    - model
    - reg_year
    - mileage
    - origin
    - province
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
                    "province_scoli",
                ]
            ],
        )
    )

    return X
