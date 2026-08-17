from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

ROOT = Path(".")

MARKET = ROOT / "resources" / "market"
RESULTS = ROOT / "project1_gb_market" / "results"
FIGURES = ROOT / "project1_gb_market" / "figures"

RESULTS.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)


# ============================================================
# SCENARIOS
# ============================================================

BASELINE = "Validation_Jan2020_UniformNetworkBaseline"
BESS120 = "Research_Jan2020_BEAT4_BESS120"


# ============================================================
# READ NATIVE PYPSA-GB REDISPATCH OUTPUTS
# ============================================================

base_path = MARKET / f"{BASELINE}_redispatch_summary.csv"
case_path = MARKET / f"{BESS120}_redispatch_summary.csv"

base = pd.read_csv(base_path)
case = pd.read_csv(case_path)

required_cols = [
    "component",
    "carrier",
    "increase_MWh",
    "decrease_MWh",
    "offer_cost",
    "bid_cost",
    "net_cost",
]

missing_base = [
    c for c in required_cols
    if c not in base.columns
]

missing_case = [
    c for c in required_cols
    if c not in case.columns
]

if missing_base:
    raise ValueError(
        f"Missing columns in baseline redispatch file: "
        f"{missing_base}"
    )

if missing_case:
    raise ValueError(
        f"Missing columns in 120 MW redispatch file: "
        f"{missing_case}"
    )

base = base[required_cols].copy()
case = case[required_cols].copy()


# ============================================================
# AGGREGATE BY INDIVIDUAL ASSET
# ============================================================

base = (
    base
    .groupby(
        ["component", "carrier"],
        as_index=False,
    )
    .agg(
        {
            "increase_MWh": "sum",
            "decrease_MWh": "sum",
            "offer_cost": "sum",
            "bid_cost": "sum",
            "net_cost": "sum",
        }
    )
)

case = (
    case
    .groupby(
        ["component", "carrier"],
        as_index=False,
    )
    .agg(
        {
            "increase_MWh": "sum",
            "decrease_MWh": "sum",
            "offer_cost": "sum",
            "bid_cost": "sum",
            "net_cost": "sum",
        }
    )
)


# ============================================================
# JOIN BASELINE AND 120 MW CASE
# ============================================================

comparison = case.merge(
    base,
    on=["component", "carrier"],
    how="outer",
    suffixes=("_120", "_base"),
)

numeric_cols = [
    "increase_MWh_120",
    "decrease_MWh_120",
    "offer_cost_120",
    "bid_cost_120",
    "net_cost_120",
    "increase_MWh_base",
    "decrease_MWh_base",
    "offer_cost_base",
    "bid_cost_base",
    "net_cost_base",
]

for col in numeric_cols:
    comparison[col] = (
        pd.to_numeric(
            comparison[col],
            errors="coerce",
        )
        .fillna(0.0)
    )


# ============================================================
# CALCULATE DIFFERENCES
# ============================================================

comparison["delta_up_MWh"] = (
    comparison["increase_MWh_120"]
    - comparison["increase_MWh_base"]
)

comparison["delta_down_MWh"] = (
    comparison["decrease_MWh_120"]
    - comparison["decrease_MWh_base"]
)

comparison["delta_offer_cost"] = (
    comparison["offer_cost_120"]
    - comparison["offer_cost_base"]
)

comparison["delta_bid_cost"] = (
    comparison["bid_cost_120"]
    - comparison["bid_cost_base"]
)

comparison["delta_cost"] = (
    comparison["net_cost_120"]
    - comparison["net_cost_base"]
)

comparison["gross_change_MWh"] = (
    comparison["delta_up_MWh"].abs()
    + comparison["delta_down_MWh"].abs()
)


# ============================================================
# KEEP CCGT + PUMPED STORAGE ONLY
# ============================================================

selected = comparison[
    comparison["carrier"]
    .astype(str)
    .str.contains(
        "CCGT|Pumped Storage",
        case=False,
        regex=True,
        na=False,
    )
].copy()


# ============================================================
# SELECT MOST IMPORTANT ASSETS
# ============================================================

selected = (
    selected
    .sort_values(
        "gross_change_MWh",
        ascending=False,
    )
    .head(12)
    .copy()
)

if selected.empty:
    raise ValueError(
        "No CCGT or pumped-storage assets found."
    )


# ============================================================
# SAVE UNDERLYING DATA
# ============================================================

output_csv = (
    RESULTS
    / "asset_redispatch_120mw.csv"
)

selected.to_csv(
    output_csv,
    index=False,
)


# ============================================================
# PREPARE LABELS
# ============================================================

selected["plot_label"] = selected.apply(
    lambda row:
        f"{row['component']} "
        f"(Δcost {row['delta_cost']/1000:+.0f}k)",
    axis=1,
)

# Sort ascending so largest asset appears near the top
# of the horizontal chart.
plot_data = (
    selected
    .sort_values(
        "gross_change_MWh",
        ascending=True,
    )
    .copy()
)

# Convert MWh to GWh.
plot_data["delta_up_GWh"] = (
    plot_data["delta_up_MWh"] / 1000
)

plot_data["delta_down_GWh"] = (
    plot_data["delta_down_MWh"] / 1000
)


# ============================================================
# FIGURE
# ============================================================

y = np.arange(len(plot_data))
bar_height = 0.36

plt.figure(
    figsize=(12, 7.5)
)

plt.barh(
    y - bar_height / 2,
    plot_data["delta_up_GWh"],
    height=bar_height,
    label="Change in upward BM redispatch",
)

plt.barh(
    y + bar_height / 2,
    plot_data["delta_down_GWh"],
    height=bar_height,
    label="Change in downward BM redispatch",
)

plt.axvline(
    0,
    linestyle="--",
    linewidth=1,
)

plt.yticks(
    y,
    plot_data["plot_label"],
)

plt.xlabel(
    "Change in redispatch relative to baseline (GWh)"
)

plt.ylabel(
    "Asset"
)

plt.title(
    "120 MW / 240 MWh BESS counterfactual:\n"
    "redistribution of balancing actions"
)

plt.legend()

plt.grid(
    axis="x",
    alpha=0.25,
)

plt.tight_layout()


# ============================================================
# SAVE FIGURE
# ============================================================

output_figure = (
    FIGURES
    / "asset_level_redispatch_120mw.png"
)

plt.savefig(
    output_figure,
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# TERMINAL SUMMARY
# ============================================================

print()
print("=" * 105)

print(
    "120 MW / 240 MWh BESS - "
    "ASSET LEVEL REDISPATCH DIAGNOSTIC"
)

print("=" * 105)

terminal_table = (
    selected
    .sort_values(
        "gross_change_MWh",
        ascending=False,
    )
    [
        [
            "component",
            "carrier",
            "delta_up_MWh",
            "delta_down_MWh",
            "delta_cost",
        ]
    ]
)

print(
    terminal_table.to_string(
        index=False,
        formatters={
            "delta_up_MWh":
                "{:,.2f}".format,

            "delta_down_MWh":
                "{:,.2f}".format,

            "delta_cost":
                "£{:,.2f}".format,
        },
    )
)

print()

print(
    f"Saved data   -> "
    f"{output_csv}"
)

print(
    f"Saved figure -> "
    f"{output_figure}"
)

print()

print("=" * 105)