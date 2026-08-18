from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS = PROJECT_ROOT / "results"
FIGURES = PROJECT_ROOT / "figures"

RESULTS.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

# ============================================================
# RESULTS FROM COMPLETED NATIVE PYPSA-GB RUNS
# ============================================================

data = [
    {
        "bess_mw": 0,
        "bess_mwh": 0,
        "constraint_cost": 41_644_919.04,
        "system_increase_mwh": 979_911.59,
        "system_decrease_mwh": 979_911.59,
        "wind_down_mwh": 324_084.49,
        "ccgt_up_mwh": 806_431.01,
        "wholesale_charge_mwh": 0.0,
        "wholesale_discharge_mwh": 0.0,
        "bm_bess_increase_mwh": 0.0,
        "bm_bess_decrease_mwh": 0.0,
    },
    {
        "bess_mw": 50,
        "bess_mwh": 100,
        "constraint_cost": 42_204_086.74,
        "system_increase_mwh": 994_126.98,
        "system_decrease_mwh": 994_126.98,
        "wind_down_mwh": 322_349.89,
        "ccgt_up_mwh": 817_297.85,
        "wholesale_charge_mwh": 1_536.45,
        "wholesale_discharge_mwh": 1_411.84,
        "bm_bess_increase_mwh": 0.0,
        "bm_bess_decrease_mwh": 0.0,
    },
    {
        "bess_mw": 70,
        "bess_mwh": 140,
        "constraint_cost": 42_147_517.26,
        "system_increase_mwh": 992_980.37,
        "system_decrease_mwh": 992_980.37,
        "wind_down_mwh": 321_846.33,
        "ccgt_up_mwh": 816_737.43,
        "wholesale_charge_mwh": 2_151.02,
        "wholesale_discharge_mwh": 1_976.58,
        "bm_bess_increase_mwh": 0.0,
        "bm_bess_decrease_mwh": 0.0,
    },
    {
        "bess_mw": 100,
        "bess_mwh": 200,
        "constraint_cost": 42_132_179.75,
        "system_increase_mwh": 993_834.03,
        "system_decrease_mwh": 993_834.03,
        "wind_down_mwh": 321_929.86,
        "ccgt_up_mwh": 817_720.11,
        "wholesale_charge_mwh": 3_072.94,
        "wholesale_discharge_mwh": 2_823.66,
        "bm_bess_increase_mwh": 0.0,
        "bm_bess_decrease_mwh": 0.0,
    },
    {
        "bess_mw": 120,
        "bess_mwh": 240,
        "constraint_cost": 42_114_782.35,
        "system_increase_mwh": 992_462.64,
        "system_decrease_mwh": 992_462.64,
        "wind_down_mwh": 321_544.75,
        "ccgt_up_mwh": 816_761.37,
        "wholesale_charge_mwh": 3_687.63,
        "wholesale_discharge_mwh": 3_388.34,
        "bm_bess_increase_mwh": 0.0,
        "bm_bess_decrease_mwh": 0.0,
    },
]

df = pd.DataFrame(data)

# ============================================================
# DERIVED METRICS
# ============================================================

baseline_cost = df.loc[df["bess_mw"] == 0, "constraint_cost"].iloc[0]
baseline_wind = df.loc[df["bess_mw"] == 0, "wind_down_mwh"].iloc[0]
baseline_ccgt = df.loc[df["bess_mw"] == 0, "ccgt_up_mwh"].iloc[0]
baseline_redispatch = df.loc[df["bess_mw"] == 0, "system_increase_mwh"].iloc[0]

df["constraint_cost_change"] = df["constraint_cost"] - baseline_cost
df["constraint_cost_change_pct"] = (
    df["constraint_cost_change"] / baseline_cost * 100
)

df["wind_down_reduction_mwh"] = baseline_wind - df["wind_down_mwh"]

df["ccgt_up_change_mwh"] = df["ccgt_up_mwh"] - baseline_ccgt

df["redispatch_change_mwh"] = (
    df["system_increase_mwh"] - baseline_redispatch
)

df["battery_throughput_mwh"] = (
    df["wholesale_charge_mwh"] + df["wholesale_discharge_mwh"]
)

# Equivalent full cycles based on discharge energy / nominal energy capacity.
df["equivalent_discharge_cycles"] = 0.0

mask = df["bess_mwh"] > 0

df.loc[mask, "equivalent_discharge_cycles"] = (
    df.loc[mask, "wholesale_discharge_mwh"]
    / df.loc[mask, "bess_mwh"]
)

# Constraint cost penalty per MW of added BESS
df["cost_change_per_mw"] = 0.0

mask = df["bess_mw"] > 0

df.loc[mask, "cost_change_per_mw"] = (
    df.loc[mask, "constraint_cost_change"]
    / df.loc[mask, "bess_mw"]
)

# Avoided wind-down per MW
df["wind_reduction_per_mw"] = 0.0

df.loc[mask, "wind_reduction_per_mw"] = (
    df.loc[mask, "wind_down_reduction_mwh"]
    / df.loc[mask, "bess_mw"]
)

# ============================================================
# SAVE FULL TABLE
# ============================================================

output = RESULTS / "bess_sweep_summary.csv"
df.to_csv(output, index=False)

# ============================================================
# PRINT RESEARCH SUMMARY
# ============================================================

print()
print("=" * 105)
print("GB MARKET DESIGN - BEAT4- BESS CAPACITY SWEEP")
print("=" * 105)

display_cols = [
    "bess_mw",
    "bess_mwh",
    "constraint_cost",
    "constraint_cost_change",
    "constraint_cost_change_pct",
    "wind_down_reduction_mwh",
    "ccgt_up_change_mwh",
    "redispatch_change_mwh",
    "wholesale_charge_mwh",
    "wholesale_discharge_mwh",
    "equivalent_discharge_cycles",
]

print(
    df[display_cols].to_string(
        index=False,
        formatters={
            "constraint_cost": "{:,.2f}".format,
            "constraint_cost_change": "{:,.2f}".format,
            "constraint_cost_change_pct": "{:.3f}".format,
            "wind_down_reduction_mwh": "{:,.2f}".format,
            "ccgt_up_change_mwh": "{:,.2f}".format,
            "redispatch_change_mwh": "{:,.2f}".format,
            "wholesale_charge_mwh": "{:,.2f}".format,
            "wholesale_discharge_mwh": "{:,.2f}".format,
            "equivalent_discharge_cycles": "{:.2f}".format,
        }
    )
)

print()
print("BASELINE CONSTRAINT COST")
print(f"£{baseline_cost:,.2f}")

best_cost_case = df.loc[df["constraint_cost"].idxmin()]
best_bess_cost_case = df[df["bess_mw"] > 0].loc[
    df[df["bess_mw"] > 0]["constraint_cost"].idxmin()
]

best_wind_case = df.loc[df["wind_down_mwh"].idxmin()]

print()
print("LOWEST COST OF ADDED-BESS CASES")
print(
    f"{best_bess_cost_case['bess_mw']:.0f} MW / "
    f"{best_bess_cost_case['bess_mwh']:.0f} MWh"
)
print(f"£{best_bess_cost_case['constraint_cost']:,.2f}")
print(
    f"Change from no-additional-BESS baseline: "
    f"£{best_bess_cost_case['constraint_cost_change']:,.2f}"
)

print()
print("LARGEST WIND DOWNWARD REDISPATCH REDUCTION")
print(
    f"{best_wind_case['bess_mw']:.0f} MW / "
    f"{best_wind_case['bess_mwh']:.0f} MWh"
)
print(
    f"{best_wind_case['wind_down_reduction_mwh']:,.2f} MWh avoided"
)

print()
print("NEW BESS BALANCING-MECHANISM MOVEMENT")
print(
    f"Total BM increase: "
    f"{df['bm_bess_increase_mwh'].sum():,.2f} MWh"
)
print(
    f"Total BM decrease: "
    f"{df['bm_bess_decrease_mwh'].sum():,.2f} MWh"
)

print()
print(f"Saved summary -> {output}")

# ============================================================
# FIGURE 1 - CONSTRAINT COST
# ============================================================

plt.figure(figsize=(8, 5))

plt.plot(
    df["bess_mw"],
    df["constraint_cost"] / 1_000_000,
    marker="o",
)

plt.axhline(
    baseline_cost / 1_000_000,
    linestyle="--",
)

plt.xlabel("Additional BESS power at BEAT4- (MW)")
plt.ylabel("Balancing / constraint cost (£ million)")
plt.title("Constraint cost response to additional BESS capacity")
plt.grid(alpha=0.3)
plt.tight_layout()

file1 = FIGURES / "bess_sweep_constraint_cost.png"
plt.savefig(file1, dpi=300)
plt.close()

# ============================================================
# FIGURE 2 - WIND REDISPATCH
# ============================================================

plt.figure(figsize=(8, 5))

plt.plot(
    df["bess_mw"],
    df["wind_down_reduction_mwh"] / 1000,
    marker="o",
)

plt.axhline(0, linestyle="--")

plt.xlabel("Additional BESS power at BEAT4- (MW)")
plt.ylabel("Reduction in wind downward redispatch (GWh)")
plt.title("Renewable constraint relief from additional BESS")
plt.grid(alpha=0.3)
plt.tight_layout()

file2 = FIGURES / "bess_sweep_wind_reduction.png"
plt.savefig(file2, dpi=300)
plt.close()

# ============================================================
# FIGURE 3 - SYSTEM REDISPATCH RESPONSE
# ============================================================

plt.figure(figsize=(8, 5))

plt.plot(
    df["bess_mw"],
    df["ccgt_up_change_mwh"] / 1000,
    marker="o",
    label="Change in CCGT upward redispatch",
)

plt.plot(
    df["bess_mw"],
    df["redispatch_change_mwh"] / 1000,
    marker="o",
    label="Change in total upward redispatch",
)

plt.axhline(0, linestyle="--")

plt.xlabel("Additional BESS power at BEAT4- (MW)")
plt.ylabel("Change from baseline (GWh)")
plt.title("Redispatch response to additional BESS")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

file3 = FIGURES / "bess_sweep_redispatch.png"
plt.savefig(file3, dpi=300)
plt.close()

# ============================================================
# FIGURE 4 - WHOLESALE BESS ACTIVITY
# ============================================================

plt.figure(figsize=(8, 5))

plt.plot(
    df["bess_mw"],
    df["wholesale_charge_mwh"] / 1000,
    marker="o",
    label="Wholesale charging",
)

plt.plot(
    df["bess_mw"],
    df["wholesale_discharge_mwh"] / 1000,
    marker="o",
    label="Wholesale discharging",
)

plt.xlabel("Additional BESS power at BEAT4- (MW)")
plt.ylabel("Monthly energy (GWh)")
plt.title("Wholesale dispatch of added BESS")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

file4 = FIGURES / "bess_sweep_wholesale_operation.png"
plt.savefig(file4, dpi=300)
plt.close()

print()
print("FIGURES SAVED")
print(file1)
print(file2)
print(file3)
print(file4)

print()
print("=" * 105)