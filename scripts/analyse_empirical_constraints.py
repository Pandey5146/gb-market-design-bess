from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]

DATA = (
    PROJECT
    / "data"
    / "processed"
    / "gb_empirical_daily_2022_2025.csv"
)

df = pd.read_csv(DATA)

df["date"] = pd.to_datetime(df["date"])


print("\n==============================================")
print("ANNUAL CONSTRAINT SUMMARY")
print("==============================================")

annual = (
    df.groupby("year")
    .agg(
        wind_gwh=("wind_gwh", "sum"),
        demand_gwh=("demand_gwh", "sum"),

        thermal_constraint_cost=(
            "thermal_constraints_cost",
            "sum",
        ),

        thermal_constraint_volume=(
            "thermal_constraints_volume",
            "sum",
        ),

        total_constraint_cost=(
            "total_constraint_cost",
            "sum",
        ),

        total_constraint_volume=(
            "total_constraint_volume",
            "sum",
        ),
    )
)

annual["wind_share"] = (
    annual["wind_gwh"]
    / annual["demand_gwh"]
)

print(annual)


print("\n==============================================")
print("CORRELATION MATRIX")
print("==============================================")

variables = [
    "wind_gwh",
    "demand_gwh",
    "wind_demand_ratio",
    "thermal_generation_gwh",
    "net_interconnector_gwh",
    "thermal_constraints_cost",
    "thermal_constraints_volume",
    "total_constraint_cost",
    "total_constraint_volume",
]

variables = [
    c for c in variables
    if c in df.columns
]

corr = df[variables].corr()

print(corr.round(3))


print("\n==============================================")
print("TOP 20 THERMAL CONSTRAINT COST DAYS")
print("==============================================")

top_cost = (
    df.sort_values(
        "thermal_constraints_cost",
        ascending=False,
    )
    [
        [
            "date",
            "wind_gwh",
            "demand_gwh",
            "wind_demand_ratio",
            "thermal_constraints_cost",
            "thermal_constraints_volume",
            "net_interconnector_gwh",
        ]
    ]
    .head(20)
)

print(top_cost.to_string(index=False))


print("\n==============================================")
print("TOP 20 THERMAL CONSTRAINT VOLUME DAYS")
print("==============================================")

top_volume = (
    df.sort_values(
        "thermal_constraints_volume",
        ascending=False,
    )
    [
        [
            "date",
            "wind_gwh",
            "demand_gwh",
            "wind_demand_ratio",
            "thermal_constraints_cost",
            "thermal_constraints_volume",
            "net_interconnector_gwh",
        ]
    ]
    .head(20)
)

print(top_volume.to_string(index=False))


print("\n==============================================")
print("HIGH WIND REGIME")
print("==============================================")

q75 = df["wind_gwh"].quantile(0.75)
q90 = df["wind_gwh"].quantile(0.90)

normal = df[df["wind_gwh"] < q75]
high = df[
    (df["wind_gwh"] >= q75)
    & (df["wind_gwh"] < q90)
]
extreme = df[df["wind_gwh"] >= q90]


def regime_stats(name, data):

    print(f"\n{name}")
    print("Days:", len(data))

    print(
        "Mean wind:",
        round(data["wind_gwh"].mean(), 2),
        "GWh",
    )

    print(
        "Mean thermal constraint cost:",
        round(
            data["thermal_constraints_cost"].mean(),
            2,
        ),
    )

    print(
        "Mean thermal constraint volume:",
        round(
            data["thermal_constraints_volume"].mean(),
            2,
        ),
    )


regime_stats("Normal wind", normal)
regime_stats("High wind", high)
regime_stats("Extreme wind", extreme)


print("\n==============================================")
print("EXTREME WIND + EXTREME CONSTRAINT DAYS")
print("==============================================")

wind90 = df["wind_gwh"].quantile(0.90)

constraint90 = (
    df["thermal_constraints_cost"]
    .quantile(0.90)
)

stress = df[
    (df["wind_gwh"] >= wind90)
    &
    (
        df["thermal_constraints_cost"]
        >= constraint90
    )
].copy()

stress = stress.sort_values(
    "thermal_constraints_cost",
    ascending=False,
)

print(
    stress[
        [
            "date",
            "wind_gwh",
            "demand_gwh",
            "wind_demand_ratio",
            "thermal_constraints_cost",
            "thermal_constraints_volume",
            "net_interconnector_gwh",
        ]
    ].to_string(index=False)
)