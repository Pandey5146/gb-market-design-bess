from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# PATHS
# ============================================================

PROJECT = Path(__file__).resolve().parents[1]

ELEXON_PATH = PROJECT / "data" / "processed" / "gb_market_core_2022_2025.csv"
NESO_PATH = PROJECT / "data" / "processed" / "neso_constraint_breakdown_2022_2025.csv"

OUTPUT_PATH = PROJECT / "data" / "processed" / "gb_empirical_daily_2022_2025.csv"


# ============================================================
# LOAD ELEXON
# ============================================================

print("Loading Elexon...")
elexon = pd.read_csv(ELEXON_PATH)

elexon["settlementDate"] = pd.to_datetime(elexon["settlementDate"])

print("Elexon rows:", len(elexon))
print(
    "Elexon date range:",
    elexon["settlementDate"].min(),
    "->",
    elexon["settlementDate"].max(),
)


# ============================================================
# IDENTIFY GENERATION COLUMNS
# ============================================================

generation_cols = [
    c for c in elexon.columns
    if c.startswith("generation_") and c.endswith("_mw")
]

print("\nGeneration columns:")
for c in generation_cols:
    print(" ", c)


# ============================================================
# INTERCONNECTORS
# ============================================================

interconnector_cols = [
    c for c in generation_cols
    if c.startswith("generation_int")
]

print("\nInterconnector columns:")
for c in interconnector_cols:
    print(" ", c)


# ============================================================
# CREATE SYSTEM VARIABLES
# ============================================================

# Wind
if "generation_wind_mw" in elexon.columns:
    elexon["wind_mw"] = elexon["generation_wind_mw"]
else:
    elexon["wind_mw"] = np.nan


# Thermal generation
thermal_candidates = [
    "generation_ccgt_mw",
    "generation_coal_mw",
    "generation_ocgt_mw",
    "generation_oil_mw",
]

thermal_cols = [
    c for c in thermal_candidates
    if c in elexon.columns
]

elexon["thermal_generation_mw"] = (
    elexon[thermal_cols].sum(axis=1, min_count=1)
)


# Interconnector aggregate
if interconnector_cols:
    elexon["net_interconnector_mw"] = (
        elexon[interconnector_cols].sum(axis=1, min_count=1)
    )
else:
    elexon["net_interconnector_mw"] = np.nan


# Renewable proxy
renewable_candidates = [
    "generation_wind_mw",
]

renewable_cols = [
    c for c in renewable_candidates
    if c in elexon.columns
]

elexon["renewable_generation_mw"] = (
    elexon[renewable_cols].sum(axis=1, min_count=1)
)


# ============================================================
# AGGREGATE ELEXON HALF-HOURLY -> DAILY
# ============================================================

# MW average over half-hour periods
daily_mean_cols = [
    "demand_mw",
    "wind_mw",
    "thermal_generation_mw",
    "net_interconnector_mw",
    "renewable_generation_mw",
]

daily_mean_cols = [
    c for c in daily_mean_cols
    if c in elexon.columns
]


daily_mean = (
    elexon
    .groupby("settlementDate")[daily_mean_cols]
    .mean()
)


# Maximum values useful for system stress
daily_max = (
    elexon
    .groupby("settlementDate")[
        ["demand_mw", "wind_mw"]
    ]
    .max()
    .rename(
        columns={
            "demand_mw": "peak_demand_mw",
            "wind_mw": "peak_wind_mw",
        }
    )
)


# ============================================================
# CONVERT HALF-HOURLY POWER TO DAILY ENERGY
# ============================================================

energy_variables = {
    "demand_mw": "demand_gwh",
    "wind_mw": "wind_gwh",
    "thermal_generation_mw": "thermal_generation_gwh",
    "renewable_generation_mw": "renewable_generation_gwh",
    "net_interconnector_mw": "net_interconnector_gwh",
}


daily_energy = pd.DataFrame(index=daily_mean.index)

for power_col, energy_col in energy_variables.items():

    if power_col not in elexon.columns:
        continue

    daily_energy[energy_col] = (
        elexon
        .groupby("settlementDate")[power_col]
        .sum(min_count=1)
        * 0.5
        / 1000
    )


# ============================================================
# COMBINE DAILY ELEXON METRICS
# ============================================================

daily_elexon = daily_mean.join(daily_max).join(daily_energy)

daily_elexon = daily_elexon.reset_index()
daily_elexon = daily_elexon.rename(
    columns={"settlementDate": "date"}
)


# ============================================================
# DAILY DERIVED METRICS
# ============================================================

# Wind share of demand
daily_elexon["wind_demand_ratio"] = (
    daily_elexon["wind_gwh"]
    / daily_elexon["demand_gwh"]
)


# Approximate thermal share
daily_elexon["thermal_demand_ratio"] = (
    daily_elexon["thermal_generation_gwh"]
    / daily_elexon["demand_gwh"]
)


# ============================================================
# LOAD NESO CONSTRAINT DATA
# ============================================================

print("\nLoading NESO...")
neso = pd.read_csv(NESO_PATH)

neso["date"] = pd.to_datetime(neso["date"])

print("NESO rows:", len(neso))
print(
    "NESO date range:",
    neso["date"].min(),
    "->",
    neso["date"].max(),
)


# ============================================================
# MERGE
# ============================================================

daily = pd.merge(
    daily_elexon,
    neso,
    on="date",
    how="left",
)


# ============================================================
# ADD RESEARCH VARIABLES
# ============================================================

constraint_cost_cols = [
    "reducing_largest_loss_cost",
    "increasing_system_inertia_cost",
    "voltage_constraints_cost",
    "thermal_constraints_cost",
]

constraint_volume_cols = [
    "reducing_largest_loss_volume",
    "increasing_system_inertia_volume",
    "voltage_constraints_volume",
    "thermal_constraints_volume",
]


daily["total_constraint_cost"] = (
    daily[constraint_cost_cols]
    .sum(axis=1, min_count=1)
)


daily["total_constraint_volume"] = (
    daily[constraint_volume_cols]
    .sum(axis=1, min_count=1)
)


# Thermal constraint cost per unit of thermal constraint volume
daily["thermal_constraint_cost_per_unit"] = (
    daily["thermal_constraints_cost"]
    / daily["thermal_constraints_volume"].replace(0, np.nan)
)


# Calendar fields
daily["year"] = daily["date"].dt.year
daily["month"] = daily["date"].dt.month
daily["month_name"] = daily["date"].dt.month_name()
daily["day_of_week"] = daily["date"].dt.day_name()


# ============================================================
# BASIC QA
# ============================================================

print("\n==============================================")
print("FINAL DAILY EMPIRICAL DATASET")
print("==============================================")

print("Shape:", daily.shape)
print(
    "Date range:",
    daily["date"].min(),
    "->",
    daily["date"].max()
)

print("\nRows per year:")
print(daily.groupby("year").size())

print("\nMissing NESO thermal constraint costs:")
print(daily["thermal_constraints_cost"].isna().sum())

print("\nSummary statistics:")
print(
    daily[
        [
            "demand_gwh",
            "wind_gwh",
            "wind_demand_ratio",
            "thermal_constraints_cost",
            "thermal_constraints_volume",
            "total_constraint_cost",
        ]
    ].describe()
)


# ============================================================
# SAVE
# ============================================================

daily.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nSaved:")
print(OUTPUT_PATH)