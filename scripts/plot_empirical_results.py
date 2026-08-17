from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parents[1]

DATA = PROJECT / "data" / "processed" / "gb_empirical_daily_2022_2025.csv"
FIGURES = PROJECT / "figures"

FIGURES.mkdir(exist_ok=True)

df = pd.read_csv(DATA)
df["date"] = pd.to_datetime(df["date"])

# absolute volume for magnitude plots
df["thermal_constraint_volume_abs"] = df["thermal_constraints_volume"].abs()


# ============================================================
# FIGURE 1 — WIND VS THERMAL CONSTRAINT COST
# ============================================================

plt.figure(figsize=(9, 6))

plt.scatter(
    df["wind_gwh"],
    df["thermal_constraints_cost"] / 1e6,
    alpha=0.45
)

plt.xlabel("Daily wind generation (GWh)")
plt.ylabel("Thermal constraint cost (£m/day)")
plt.title("GB Wind Generation vs Thermal Constraint Cost, 2022–2025")

plt.tight_layout()

plt.savefig(
    FIGURES / "01_wind_vs_thermal_constraint_cost.png",
    dpi=300
)

plt.close()


# ============================================================
# FIGURE 2 — WIND SHARE VS CONSTRAINT COST
# ============================================================

plt.figure(figsize=(9, 6))

plt.scatter(
    df["wind_demand_ratio"] * 100,
    df["thermal_constraints_cost"] / 1e6,
    alpha=0.45
)

plt.xlabel("Wind generation as % of daily demand")
plt.ylabel("Thermal constraint cost (£m/day)")
plt.title("Wind Penetration vs Thermal Constraint Cost, 2022–2025")

plt.tight_layout()

plt.savefig(
    FIGURES / "02_wind_share_vs_constraint_cost.png",
    dpi=300
)

plt.close()


# ============================================================
# FIGURE 3 — HIGH WIND REGIMES
# ============================================================

q75 = df["wind_gwh"].quantile(0.75)
q90 = df["wind_gwh"].quantile(0.90)

df["wind_regime"] = "Normal"

df.loc[
    (df["wind_gwh"] >= q75)
    & (df["wind_gwh"] < q90),
    "wind_regime"
] = "High"

df.loc[
    df["wind_gwh"] >= q90,
    "wind_regime"
] = "Extreme"


regime_order = ["Normal", "High", "Extreme"]

regime_cost = (
    df.groupby("wind_regime")["thermal_constraints_cost"]
    .mean()
    .reindex(regime_order)
    / 1e6
)

plt.figure(figsize=(8, 6))

regime_cost.plot(kind="bar")

plt.ylabel("Average thermal constraint cost (£m/day)")
plt.xlabel("Wind regime")
plt.title("Average Thermal Constraint Cost by Wind Regime")

plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    FIGURES / "03_constraint_cost_by_wind_regime.png",
    dpi=300
)

plt.close()


# ============================================================
# FIGURE 4 — ANNUAL CONSTRAINT COST
# ============================================================

annual = (
    df.groupby("year")["thermal_constraints_cost"]
    .sum()
    / 1e9
)

plt.figure(figsize=(8, 6))

annual.plot(kind="bar")

plt.ylabel("Annual thermal constraint cost (£bn)")
plt.xlabel("Year")
plt.title("GB Annual Thermal Constraint Cost, 2022–2025")

plt.xticks(rotation=0)

plt.tight_layout()

plt.savefig(
    FIGURES / "04_annual_thermal_constraint_cost.png",
    dpi=300
)

plt.close()


# ============================================================
# FIGURE 5 — TIME SERIES
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    df["date"],
    df["thermal_constraints_cost"] / 1e6,
    linewidth=0.8
)

plt.xlabel("Date")
plt.ylabel("Thermal constraint cost (£m/day)")
plt.title("GB Daily Thermal Constraint Cost, 2022–2025")

plt.tight_layout()

plt.savefig(
    FIGURES / "05_constraint_cost_timeseries.png",
    dpi=300
)

plt.close()


print("Figures saved to:")
print(FIGURES)