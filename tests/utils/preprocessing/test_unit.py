from utils.preprocessing import (
    clean_mileage,
    clean_model,
    clean_prediction_input,
    clean_province,
    clean_reg_year,
)
import numpy as np
import pandas as pd


def test_clean_mileage():
    df_input = pd.DataFrame(
        {
            "col1": [1, 2, 3],
        }
    )
    df_output = clean_mileage(df=df_input)
    expected_output = pd.DataFrame(
        {
            "col1": np.log([1, 2, 3]),
        }
    )

    assert (
        pd.testing.assert_frame_equal(df_output, expected_output, check_dtype=False)
        is None
    )
