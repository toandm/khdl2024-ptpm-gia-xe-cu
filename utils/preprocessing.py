import json
import numpy as np
import pandas as pd


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


def transform_mileage(df: pd.DataFrame) -> pd.DataFrame:
    return np.log(df)


def transform_model(df: pd.DataFrame) -> pd.Series:
    # Get model reference price
    MODEL_REF_PRICE_PATH = "data/model_ref_price.csv"
    df_model_ref_price = pd.read_csv(MODEL_REF_PRICE_PATH)
    df_model_ref_price["ref_price_clean"] = pd.to_numeric(
        df_model_ref_price["ref_price"].str.replace(".", "")
    )

    # Join with dataframe
    output_df = df.merge(
        right=df_model_ref_price, left_on="model", right_on="model", how="left"
    )

    output_df["ref_price_clean_transform"] = np.log(
        output_df["ref_price_clean"] / 1_000
    )

    return output_df["ref_price_clean_transform"]


def transform_province(df: pd.DataFrame) -> pd.DataFrame:
    pass


def transform_reg_year(df: pd.DataFrame) -> pd.DataFrame:
    pass


def transform_prediction_input(input: dict):
    """
    Transform inputs from user and output as the model input
    Input should have these fields:
    - model
    - reg_year
    - mileage
    - origin
    - province
    """
