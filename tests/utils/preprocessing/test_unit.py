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
            {"model": ["Wave", "SH", "Future"]},
            transform_model,
            {"ref_price_clean_transform": np.log([20_000, 105_000, 32_000])},
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


def test_transform_prediction_input():
    pass
