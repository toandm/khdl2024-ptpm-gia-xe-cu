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


def clean_prediction_input(input: dict):
    """
    Transform inputs from user and output as the model input
    Input should have these fields:
    - model
    - reg_year
    - mileage
    - origin
    - province
    """


def clean_mileage(df: pd.DataFrame) -> pd.DataFrame:
    return np.log(df)


def clean_model(df: pd.DataFrame) -> pd.DataFrame:
    pass


def clean_province(df: pd.DataFrame) -> pd.DataFrame:
    pass


def clean_reg_year(df: pd.DataFrame) -> pd.DataFrame:
    pass
