import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.preprocessing import PolynomialFeatures
import seaborn as sns
from utils import preprocessing as pp

INPUT_FILE_PATH = "data/input_xe_cu.csv"
COUNTRY_LOOKUP_PATH = "data/origin_country_multiplier.csv"
REF_PRICE_PATH = "data/model_ref_price.csv"
SCOLI_PATH = "data/input_scoli_2023.json"

# Config pandas
pd.options.mode.copy_on_write = True

df = pd.read_csv(INPUT_FILE_PATH)

# Clean columns
df["price_clean"] = pd.to_numeric(df["price"].str.replace("đ", "").str.replace(".", ""))
df["province"] = df["location"].str.split(", ").apply(lambda x: x[-1])
df["province_clean"] = df["province"].case_when(
    caselist=[
        (df["province"].eq("Tp Hồ Chí Minh"), "TP. Hồ Chí Minh"),
        (df["province"].eq("Bà Rịa - Vũng Tàu"), "Bà Rịa-Vũng Tàu"),
        (df["province"].eq("Thừa Thiên Huế"), "Thừa Thiên - Huế"),
        (df["province"].eq("Thanh Hóa"), "Thanh Hoá"),
        (df["province"].eq("Khánh Hòa"), "Khánh Hoà"),
        (df["province"].eq("Hòa Bình"), "Hoà Bình"),
    ]
)
df["reg_year_clean"] = pd.to_numeric(
    df["reg_year"].case_when(caselist=[(df["reg_year"].eq("trước năm 1980"), 1980)])
)


# Reduce scale of price and transform to log
df["price_clean"] = df["price_clean"] / 1_000
df["price_log"] = np.log(df["price_clean"])


# Transform columns into suitable predictors
# Note that this operation should be done before filter, since
# filter will remove some indexes. Some transforms use merge, which
# reset index, making the output becomes difficult to understand.
df["mileage_log"] = pp.transform_mileage(df["mileage"])
df["model_ref_price_log"] = pp.transform_model(df["model"])
df["origin_multiplier"] = pp.transform_origin(df["origin"])
df["province_scoli"] = pp.transform_province(df["province_clean"])
df["age_log"] = pp.transform_reg_year(df["reg_year_clean"])


# Filter

## Remove vague models
df_filter = df[~df["model"].isin(["Dòng khác", "dòng khác"])]

## Price should be at least 1M. Look at offers at 600M maximum
df_filter = df_filter[
    df_filter["price_clean"].between(1_000, 600_000, inclusive="neither")
]

## Keep models with over 30 offers only
df_model_count = df_filter.groupby("model").agg(counts=("model", "count")).reset_index()

# df_model_over_n = df_model_count[df_model_count["counts"] >= 30]
df_model_over_n = df_model_count.sort_values(by="counts", ascending=False).head(10)
df_filter = df_filter[df_filter["model"].isin(df_model_over_n["model"])]

## Try keeping records with sensible mileage
df_filter = df_filter[df_filter["mileage"].between(500, 900_000)]

## Remove outliers, unreasonable price. These are either
## only the bike component, or are actually another model
df_transform = df_filter[
    ~((df_filter["model"] == "SH") & (df_filter["price_clean"] < 3_000))
]

df_select = df_transform[
    [
        "price_log",
        "age_log",
        "mileage_log",
        "model",
        "model_ref_price_log",
        "origin",
        "origin_multiplier",
        "province_clean",
        "province_scoli",
    ]
]

df_final = df_select

# Linear regression models
y = df_final["price_log"]

# Polynomial for age_log
poly = PolynomialFeatures(degree=3)
age_log_poly_intercept = poly.fit_transform(df_final[["age_log"]])

# Polynomial regression with mileage
X = np.hstack(
    (
        age_log_poly_intercept,
        df_final[["mileage_log", "origin_multiplier", "model_ref_price_log"]],
    )
)

lin_model = sm.OLS(y, X).fit()
print(f"{lin_model.summary()=}")
# sns.regplot(
#     x=lin_model.fittedvalues,
#     y=lin_model.get_influence().resid_studentized_internal,
#     lowess=True,
#     line_kws={"color": "red"},
# )
# plt.show()


X2 = np.hstack(
    (
        age_log_poly_intercept,
        df_final[
            [
                "mileage_log",
                "origin_multiplier",
                "model_ref_price_log",
                "province_scoli",
            ]
        ],
    )
)

lin_model2 = sm.OLS(y, X2).fit()
print(f"{lin_model2.summary()=}")

# Predict
# Create new data for prediction
new_data = {
    "model": ["SH"],
    "reg_year": [2020],
    "mileage": [10_000],
    "origin": ["Việt Nam"],
    "province": ["Hà Nội"],
}

X_new = pp.transform_prediction_input(input=new_data)

# Predict and exponentiate the result
predicted_price = np.exp(lin_model.predict(X_new)) * 1_000
print(f"{predicted_price[0]=: ,}")

d = 1
