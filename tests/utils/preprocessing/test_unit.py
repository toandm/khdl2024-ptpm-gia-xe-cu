from utils.preprocessing import (
    transform_mileage,
    transform_model,
    transform_origin,
    transform_province,
    transform_reg_year,
    transform_prediction_input,
)
import numpy as np
import pandas as pd
import pytest


@pytest.mark.parametrize(
    "input_dict, fn, expected_output_dict",
    [
        (
            {"mileage": [1, 2, 3]},
            transform_mileage,
            {"mileage_log": np.log([1, 2, 3])},
        ),
        (
            {"model": ["Dream", "Mio", "Nouvo"]},
            transform_model,
            {"price_avg_log": np.log([15_000, 26_000, 35_000])},
        ),
        (
            {"origin": ["Hàn Quốc", "Việt Nam", "Thái Lan"]},
            transform_origin,
            {"country_multiplier": [3, 1, 2]},
        ),
        (
            {"province": ["TP. Hồ Chí Minh", "Hà Nội", "Thừa Thiên - Huế"]},
            transform_province,
            {"province_scoli": [98.44, 100, 93.65]},
        ),
        (
            {"reg_year": [2013, 2025, 2006]},
            transform_reg_year,
            {"age_log": np.log([12, 0.5, 19])},
        ),
    ],
)
def test_transform(input_dict: dict, fn, expected_output_dict: dict):
    df_input = pd.DataFrame(input_dict)
    df_output = fn(df_col=df_input.iloc[:, 0]).to_frame()
    expected_output = pd.DataFrame(expected_output_dict)
    assert (
        pd.testing.assert_frame_equal(df_output, expected_output, check_dtype=False)
        is None
    )


@pytest.fixture
def input_dict() -> dict:
    return {
        "mileage": [10_000],
        "model": ["SH"],
        "origin": ["Việt Nam"],
        "province": ["Hà Nội"],
        "reg_year": [2021],
    }


def test_transform_prediction_input(input_dict):
    expected_output = np.array(
        [
            [
                1,  # age_log polynomials
                np.log(4) ** 1,
                np.log(4) ** 2,
                np.log(4) ** 3,
                np.log(10_000),  # mileage log
                1,  # origin_multiplier
                np.log(105_000),  # model_ref_price_log
                100,  # province_scoli
            ]
        ]
    )
    output = transform_prediction_input(input=input_dict)
    assert np.testing.assert_array_equal(output, expected_output) is None
