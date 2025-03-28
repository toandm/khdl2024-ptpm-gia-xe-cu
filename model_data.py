import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.preprocessing import PolynomialFeatures
import seaborn as sns
from utils.preprocessing import read_json_stat

INPUT_FILE_PATH = "data/input_xe_cu.csv"
COUNTRY_LOOKUP_PATH = "data/country_price_multiplier.csv"
REF_PRICE_PATH = "data/model_ref_price.csv"
SCOLI_PATH = "data/input_scoli_2023.json"

# Config pandas
pd.options.mode.copy_on_write = True

df_input = pd.read_csv(INPUT_FILE_PATH)
df_countries = pd.read_csv(COUNTRY_LOOKUP_PATH)
df_ref_price = pd.read_csv(REF_PRICE_PATH)
df_scoli = read_json_stat(file_path=SCOLI_PATH)

# Join with country lookup
df = df_input.merge(
    right=df_countries, left_on="origin", right_on="country_name", how="left"
).merge(right=df_ref_price, left_on="model", right_on="model", how="left")

# Clean columns
df["price_clean"] = pd.to_numeric(df["price"].str.replace("đ", "").str.replace(".", ""))
df["ref_price_clean"] = pd.to_numeric(df["ref_price"].str.replace(".", ""))
df["location_clean"] = df["location"].str.split(", ").apply(lambda x: x[-1])
df["reg_year_clean"] = pd.to_numeric(
    df["reg_year"].case_when(caselist=[(df["reg_year"].eq("trước năm 1980"), 1980)])
)

# Reduce scale of price
df["price_clean"] = df["price_clean"] / 1_000
df["ref_price_clean"] = df["ref_price_clean"] / 1_000

# Add age
df["age"] = 2025 - df["reg_year_clean"]
# Move age = 0 to age = 0.5 since the bike must have some age
df["age_updated"] = df["age"].case_when(caselist=[(df["age"].eq(0), 0.5)])

# Filter

## Remove vague models
df_filter = df[~df["model"].isin(["Dòng khác", "dòng khác"])]

## Price should be at least 1M. Look at offers at 600M maximum
df_filter = df_filter[
    df_filter["price_clean"].between(1_000, 600_000, inclusive="neither")
]

## Keep models with over 30 offers only
df_model_count = df_filter.groupby("model").agg(counts=("model", "count")).reset_index()

df_model_over_n = df_model_count[df_model_count["counts"] >= 30]
# df_model_over_n = df_model_count.sort_values(by="counts", ascending=False).head(10)
df_filter = df_filter[df_filter["model"].isin(df_model_over_n["model"])]

## Try keeping records with sensible mileage
df_filter = df_filter[df_filter["mileage"].between(500, 900_000)]

## Remove outliers, unreasonable price. These are either
## only the bike component, or are actually another model
df_filter = df_filter[
    ~((df_filter["model"] == "SH") & (df_filter["price_clean"] < 3000))
]

df_transform = df_filter[
    ~(
        (df_filter["model"] == "SH")
        & (df_filter["age_updated"] <= 5)
        & (df_filter["price_clean"] < 20000)
    )
]

# Log transform
df_transform["price_log"] = np.log(df_transform["price_clean"])
df_transform["ref_price_log"] = np.log(df_transform["ref_price_clean"])
df_transform["age_log"] = np.log(df_transform["age_updated"])
df_transform["mileage_log"] = np.log(df_transform["mileage"])

df_select = df_transform[
    [
        "price_log",
        "age_log",
        "mileage_log",
        "model",
        "ref_price_log",
        "origin",
        "country_multiplier",
        "location_clean",
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
        df_final[["mileage_log", "country_multiplier", "ref_price_log"]],
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


# Predict
# Create new data for prediction
new_data = pd.DataFrame(
    {
        "age_log": [np.log(4)],
        "mileage_log": [np.log(10_000)],
        "country_multiplier": [1],
        "ref_price_log": [np.log(105_000)],
    }
)

# Add polynomial features for age_log
age_log_poly = poly.fit_transform(new_data[["age_log"]])

# Combine polynomial features with other predictors
X_new = np.hstack(
    (
        age_log_poly,
        new_data[["mileage_log", "country_multiplier", "ref_price_log"]],
    )
)

# Predict and exponentiate the result
predicted_price = np.exp(lin_model.predict(X_new)) * 1_000
print(f"{predicted_price[0]=: ,}")

d = 1
