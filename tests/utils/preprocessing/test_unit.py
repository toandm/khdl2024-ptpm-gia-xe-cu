from utils.preprocessing import (
    transform_mileage,
    transform_model,
    transform_prediction_input,
    transform_province,
    transform_reg_year,
)
import numpy as np
import pandas as pd


def test_transform_mileage():
    df_input = pd.DataFrame(
        {
            "mileage": [1, 2, 3],
        }
    )
    df_output = transform_mileage(df=df_input)
    expected_output = pd.DataFrame(
        {
            "mileage": np.log([1, 2, 3]),
        }
    )

    assert (
        pd.testing.assert_frame_equal(df_output, expected_output, check_dtype=False)
        is None
    )


def test_transform_model():
    df_input = pd.DataFrame(
        {
            "model": ["Wave", "SH", "Future"],
        }
    )
    df_output = transform_model(df=df_input).to_frame()
    expected_output = pd.DataFrame(
        {
            "ref_price_clean_transform": np.log([20_000, 105_000, 32_000]),
        }
    )

    assert (
        pd.testing.assert_frame_equal(df_output, expected_output, check_dtype=False)
        is None
    )
