from sklearn.preprocessing import PolynomialFeatures
from utils import preprocessing as pp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import seaborn as sns
import statsmodels.api as sm
from sklearn.model_selection import train_test_split

INPUT_FILE_PATH = "data/input_xe_cu.csv"
ORIGIN_MAPPING = {
    "Thái Lan": ["thái", "thai lan", "xe thái"],
    "Nhật Bản": ["nhật", "nhat ban", "xe nhật"],
    "Indonesia": ["indonesia", "xe indo"],
    "Ý": ["ý", "italia"],
    "Mỹ": ["mỹ", "america", "xe mỹ"],
    "Trung Quốc": ["trung", "xe tq", "xe trung quốc", "trung quốc"],
    "Ấn Độ": ["ấn", "xe ấn", "an do"],
    "Hàn Quốc": ["hàn", "xe hàn", "han quoc"],
    "Đức": ["đức", "xe đức", "duc"],
    "Đài Loan": ["đài", "xe đài", "dai loan"],
}

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


# Update origin from description and title
def update_origin(row):
    if row["origin"].lower() in ["đang cập nhật", "nước khác"]:
        text = f"{row['description']} {row['title']}".lower().strip()
        for country, keywords in ORIGIN_MAPPING.items():
            if any(re.search(rf"\b{keyword}\b", text) for keyword in keywords):
                return country
        return "Việt Nam"
    else:
        return row["origin"]


df["origin_updated"] = df.apply(update_origin, axis=1)

# Reduce scale of price and transform to log
df["price_clean"] = df["price_clean"] / 1_000
df["price_log"] = np.log(df["price_clean"])


# Transform columns into suitable predictors
# Note that this operation should be done before filter, since
# filter will remove some indexes. Some transforms use merge, which
# reset index, making the output becomes difficult to understand.
df["mileage_log"] = pp.transform_mileage(df["mileage"])
df["model_ref_price_log"] = pp.transform_model(df["model"])
# df["origin_multiplier"] = pp.transform_origin(df["origin"])
df["origin_multiplier"] = pp.transform_origin(df["origin_updated"])
df["province_scoli"] = pp.transform_province(df["province_clean"])
df["age_log"] = pp.transform_reg_year(df["reg_year_clean"])


# Filter

## Remove vague models
df_filter = df[~df["model"].isin(["Dòng khác", "dòng khác"])]

## Price should be at least 1M. Look at offers at 600M maximum
df_filter = df_filter[
    df_filter["price_clean"].between(1_000, 600_000, inclusive="neither")
]

## START - USE THIS PART to get reference price for all bikes
# ## Get rows with reference price only
df_filter = df_filter[df_filter["model_ref_price_log"].notnull()]

## END


# Models with over 30 offers only
df_model_count = df_filter.groupby("model").agg(counts=("model", "count")).reset_index()

## START - USE THIS PART to get reference price for top 10 bikes with most posts

df_model_over_n = df_model_count[df_model_count["counts"] >= 30]
# df_model_over_n = df_model_count.sort_values(by="counts", ascending=False).head(30)
df_filter = df_filter[df_filter["model"].isin(df_model_over_n["model"])]

## END

## Remove outliers, unreasonable price. These are either
## only the bike component, or are actually another model
df_filter = df_filter[
    ~((df_filter["model"] == "SH") & (df_filter["price_clean"] < 3_000))
]

df_filter = df_filter[~df_filter["model"].isin(["Vespa", "Cub", "R", "Dream"])]


## Try keeping records with sensible mileage
df_filter = df_filter[df_filter["mileage"].between(500, 900_000)]

# Linear regression models
y = df_filter["price_log"]

# Polynomial for age_log
poly = PolynomialFeatures(degree=3)
age_log_poly_intercept = poly.fit_transform(df_filter[["age_log"]])

# Polynomial regression with mileage
X = np.hstack(
    (
        age_log_poly_intercept,
        df_filter[
            [
                "mileage_log",
                "origin_multiplier",
                "model_ref_price_log",
                # "province_scoli",
            ]
        ],
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

# Diagnose influential points
# Ref: https://towardsdatascience.com/linear-regression-models-and-influential-points-4ee844adac6d/
# df_influence = lin_model.get_influence().summary_frame()
# # Join on index
# df_with_influence = df_filter.join(other=df_influence)

# # Number of observations
# n = len(df_influence)
# # Predictors
# k = 6
# cutoff_leverage = ((2 * k) + 2) / n
# cutoff_cooks: float = df_influence["cooks_d"].mean() * 3

# # Values with high hat values
# df_high_leverage = df_with_influence[df_with_influence["hat_diag"] >= cutoff_leverage]
# df_high_cooks_d = df_with_influence[df_with_influence["cooks_d"] >= cutoff_cooks]

# # High hat values count group by model
# df_high_leverage.groupby("model")["hat_diag"].count()
# df_model_high_leverage_count = (
#     df_high_leverage.groupby("model")["hat_diag"]
#     .count()
#     .sort_values(ascending=False)
#     .reset_index()
# )

# df_high_cooks_d.groupby("model")["cooks_d"].count()
# df_model_high_cook_count = (
#     df_high_cooks_d.groupby("model")["cooks_d"]
#     .count()
#     .sort_values(ascending=False)
#     .reset_index()
# )

# df_model_count = (
#     df_filter.groupby("model")["price_clean"]
#     .agg(counts="count")
#     .sort_values(by="counts", ascending=False)
#     .reset_index()
# )
# df_count_join = df_model_count.merge(
#     right=df_model_high_leverage_count, left_on="model", right_on="model", how="left"
# ).merge(right=df_model_high_cook_count, left_on="model", right_on="model", how="left")
# df_count_join.fillna(0, inplace=True)
# df_count_join["high_leverage_pct"] = df_count_join["hat_diag"] / df_count_join["counts"]
# df_count_join["high_cook_pct"] = df_count_join["cooks_d"] / df_count_join["counts"]
# df_count_join.sort_values("high_leverage_pct", ascending=False).head(10)

# Predict
# Create new data for prediction
# new_data = {
#     "model": ["SH"],
#     "reg_year": [2021],
#     "mileage": [10_000],
#     "origin": ["Việt Nam"],
#     "province": ["Hà Nội"],
# }

new_data = {
    "model": ["Sirius"],
    "reg_year": [2019],
    "mileage": [66_000],
    "origin": ["Việt Nam"],
    "province": ["Hà Nội"],
}

X_new = pp.transform_prediction_input(input=new_data)

# Predict and exponentiate the result
predicted_price = round(np.exp(lin_model.predict(X_new))[0]) * 1_000
print(f"{predicted_price=: ,}")

d = 1
