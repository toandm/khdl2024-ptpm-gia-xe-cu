from utils.preprocessing import (
    transform_mileage,
    transform_model,
    transform_prediction_input,
    transform_province,
    transform_reg_year,
)
import numpy as np
import pandas as pd


def test_clean_mileage():
    df_input = pd.DataFrame(
        {
            "col1": [1, 2, 3],
        }
    )
    df_output = transform_mileage(df=df_input)
    expected_output = pd.DataFrame(
        {
            "col1": np.log([1, 2, 3]),
        }
    )

    assert (
        pd.testing.assert_frame_equal(df_output, expected_output, check_dtype=False)
        is None
    )
