import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.preprocessing import PolynomialFeatures
import seaborn as sns

INPUT_FILE_PATH = "data/input_xe_cu.csv"
COUNTRY_LOOKUP_PATH = "data/country_price_multiplier.csv"
REF_PRICE_PATH = "data/model_ref_price.csv"

# Config pandas
pd.options.mode.copy_on_write = True

df_input = pd.read_csv(INPUT_FILE_PATH)
df_countries = pd.read_csv(COUNTRY_LOOKUP_PATH)
df_ref_price = pd.read_csv(REF_PRICE_PATH)

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

# df_model_over_n = df_model_count[df_model_count["counts"] >= 30]
df_model_over_n = df_model_count.sort_values(by="counts", ascending=False).head(10)
df_filter = df_filter[df_filter["model"].isin(df_model_over_n["model"])]

## Try keeping records with sensible mileage
df_transform = df_filter[df_filter["mileage"].between(500, 900_000)]

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


# Plot to check for linearity
# plt.scatter(df_final["age_log"], df_final["price_log"])
# plt.show()

# Linear regression models
X = sm.add_constant(df_final["age_log"])
y = df_final["price_log"]
m1 = sm.OLS(endog=y, exog=X).fit()
print(f"{m1.summary()=}")
# plt.scatter(df_final["age_log"], df_final["price_log"])
# plt.plot(df_final["age_log"], m1.fittedvalues, "r.")
# plt.show()

# Polynomial regression models
poly = PolynomialFeatures(degree=3)
X_poly = poly.fit_transform(df_final[["age_log"]])

# Get orthogonal polynomial like R
# Ref: https://stackoverflow.com/questions/41317127/python-equivalent-to-r-poly-function
X_ortho_poly = np.linalg.qr(X_poly)[0][:, 1:]
X_ortho_poly_intecept = sm.add_constant(X_ortho_poly)
m3 = sm.OLS(y, X_ortho_poly_intecept).fit()
print(f"{m3.summary()=}")
# plt.scatter(df_final["age_log"], df_final["price_log"])
# plt.plot(df_final["age_log"], m3.fittedvalues, "r.")
# plt.show()

# Polynomial regression with mileage
X_poly_mil = np.hstack((X_ortho_poly_intecept, df_final[["mileage_log"]]))
m3_mil = sm.OLS(y, X_poly_mil).fit()
print(f"{m3_mil.summary()=}")

# # Check standardized residual against fitted value
# sns.regplot(
#     x=m3_mil.fittedvalues,
#     y=m3_mil.get_influence().resid_studentized_internal,
#     lowess=True,
#     line_kws={"color": "red"},
# )
# plt.show()

# Polynomial regression with mileage and country multiplier
X_poly_mil_country = np.hstack((X_poly_mil, df_final[["country_multiplier"]]))
m4 = sm.OLS(y, X_poly_mil_country).fit()
print(f"{m4.summary()=}")
# sns.regplot(
#     x=m4.fittedvalues,
#     y=m4.get_influence().resid_studentized_internal,
#     lowess=True,
#     line_kws={"color": "red"},
# )
# plt.show()

# Polynomial regression with mileage, country multiplier, and ref price
X_poly_mil_country_ref = np.hstack((X_poly_mil_country, df_final[["ref_price_log"]]))
m5 = sm.OLS(y, X_poly_mil_country_ref).fit()
print(f"{m5.summary()=}")
# sns.regplot(
#     x=m5.fittedvalues,
#     y=m5.get_influence().resid_studentized_internal,
#     lowess=True,
#     line_kws={"color": "red"},
# )
# plt.show()

# AIC and BIC
print(
    (
        m3.aic,
        m3_mil.aic,
        m4.aic,
        m5.aic,
    )
)

print(
    (
        m3.bic,
        m3_mil.bic,
        m4.bic,
        m5.bic,
    )
)

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
predicted_price = np.exp(m5.predict(X_new)) * 1_000
print(f"{predicted_price[0]=: ,}")

d = 1
