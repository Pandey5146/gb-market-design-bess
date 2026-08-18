from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import pypsa


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PYPSA_GB_ROOT = PROJECT_ROOT.parent / "PyPSA-GB"

MARKET = PYPSA_GB_ROOT / "resources" / "market"
NETWORK = PYPSA_GB_ROOT / "resources" / "network"

RESULTS = PROJECT_ROOT / "results"
FIGURES = PROJECT_ROOT / "figures"

RESULTS.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)


SCENARIOS = {
    0: "Validation_Jan2020_UniformNetworkBaseline",
    50: "Research_Jan2020_BEAT4_BESS50",
    70: "Research_Jan2020_BEAT4_BESS70",
    100: "Research_Jan2020_BEAT4_BESS100",
    120: "Research_Jan2020_BEAT4_BESS120",
}


def read_dispatch(path):
    df = pd.read_csv(path, index_col=0)

    # Convert all dispatch values to numeric.
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(axis=1, how="all")

    return df


def infer_snapshot_hours(index):
    try:
        dt = pd.to_datetime(index)
        differences = pd.Series(dt).diff().dropna()

        if len(differences) > 0:
            hours = differences.median().total_seconds() / 3600
            if hours > 0:
                return hours
    except Exception:
        pass

    # January 2020 market run is half-hourly.
    return 0.5


def analyse_scenario(bess_mw, scenario):
    print()
    print("=" * 90)
    print(f"Reading {bess_mw} MW case: {scenario}")
    print("=" * 90)

    network_path = NETWORK / f"{scenario}.nc"

    wholesale_path = MARKET / f"{scenario}_wholesale_dispatch.csv"
    physical_path = MARKET / f"{scenario}_balancing_dispatch.csv"

    n = pypsa.Network(network_path)

    wholesale = read_dispatch(wholesale_path)
    physical = read_dispatch(physical_path)

    common_generators = [
        g for g in wholesale.columns
        if g in physical.columns and g in n.generators.index
    ]

    print(f"Wholesale generators: {len(wholesale.columns)}")
    print(f"Physical generators:  {len(physical.columns)}")
    print(f"Matched generators:   {len(common_generators)}")

    wholesale = wholesale[common_generators]
    physical = physical[common_generators]

    # Ensure identical snapshot length.
    common_index = wholesale.index.intersection(physical.index)

    wholesale = wholesale.loc[common_index]
    physical = physical.loc[common_index]

    snapshot_hours = infer_snapshot_hours(common_index)

    print(f"Snapshot duration:     {snapshot_hours:.3f} hours")

    # --------------------------------------------------------
    # Generator-level energy
    # --------------------------------------------------------

    wholesale_energy = wholesale.sum(axis=0) * snapshot_hours
    physical_energy = physical.sum(axis=0) * snapshot_hours

    difference = physical - wholesale

    bm_increase = (
        difference.clip(lower=0).sum(axis=0)
        * snapshot_hours
    )

    bm_decrease = (
        (-difference.clip(upper=0)).sum(axis=0)
        * snapshot_hours
    )

    generator_result = pd.DataFrame({
        "generator": common_generators,
        "carrier": n.generators.loc[
            common_generators, "carrier"
        ].values,
        "wholesale_mwh": wholesale_energy.values,
        "physical_mwh": physical_energy.values,
        "bm_increase_mwh": bm_increase.values,
        "bm_decrease_mwh": bm_decrease.values,
    })

    # --------------------------------------------------------
    # Aggregate by carrier
    # --------------------------------------------------------

    carrier_result = (
        generator_result
        .groupby("carrier", as_index=False)
        .agg({
            "wholesale_mwh": "sum",
            "physical_mwh": "sum",
            "bm_increase_mwh": "sum",
            "bm_decrease_mwh": "sum",
        })
    )

    carrier_result["bess_mw"] = bess_mw
    carrier_result["scenario"] = scenario

    return carrier_result


# ============================================================
# RUN ALL FIVE COMPLETED CASES
# ============================================================

all_results = []

for bess_mw, scenario in SCENARIOS.items():
    result = analyse_scenario(bess_mw, scenario)
    all_results.append(result)

carrier = pd.concat(all_results, ignore_index=True)

raw_file = RESULTS / "carrier_dispatch_by_scenario.csv"
carrier.to_csv(raw_file, index=False)

print()
print(f"Saved raw carrier results -> {raw_file}")


# ============================================================
# COMPARE EACH CASE AGAINST BASELINE
# ============================================================

metrics = [
    "wholesale_mwh",
    "physical_mwh",
    "bm_increase_mwh",
    "bm_decrease_mwh",
]

baseline = (
    carrier[carrier["bess_mw"] == 0]
    .set_index("carrier")[metrics]
)

comparisons = []

for bess_mw in sorted(SCENARIOS.keys()):

    current = (
        carrier[carrier["bess_mw"] == bess_mw]
        .set_index("carrier")[metrics]
    )

    joined = current.join(
        baseline,
        how="outer",
        lsuffix="",
        rsuffix="_baseline",
    ).fillna(0)

    for metric in metrics:
        joined[f"delta_{metric}"] = (
            joined[metric]
            - joined[f"{metric}_baseline"]
        )

    joined["bess_mw"] = bess_mw
    joined["carrier"] = joined.index

    comparisons.append(joined.reset_index(drop=True))


comparison = pd.concat(comparisons, ignore_index=True)

comparison_file = RESULTS / "carrier_dispatch_diagnostic.csv"
comparison.to_csv(comparison_file, index=False)

print(f"Saved comparison -> {comparison_file}")


# ============================================================
# CCGT DIAGNOSTIC
# ============================================================

ccgt = comparison[
    comparison["carrier"]
    .astype(str)
    .str.contains("CCGT", case=False, na=False)
].copy()

ccgt_summary = (
    ccgt.groupby("bess_mw", as_index=False)
    .agg({
        "delta_wholesale_mwh": "sum",
        "delta_physical_mwh": "sum",
        "delta_bm_increase_mwh": "sum",
        "delta_bm_decrease_mwh": "sum",
    })
)

print()
print("=" * 90)
print("CCGT: CHANGE FROM NO-ADDITIONAL-BESS BASELINE")
print("=" * 90)

print(
    ccgt_summary.to_string(
        index=False,
        formatters={
            "delta_wholesale_mwh": "{:,.2f}".format,
            "delta_physical_mwh": "{:,.2f}".format,
            "delta_bm_increase_mwh": "{:,.2f}".format,
            "delta_bm_decrease_mwh": "{:,.2f}".format,
        }
    )
)


# ============================================================
# WIND DIAGNOSTIC
# ============================================================

wind = comparison[
    comparison["carrier"]
    .astype(str)
    .str.contains("wind", case=False, na=False)
].copy()

wind_summary = (
    wind.groupby("bess_mw", as_index=False)
    .agg({
        "delta_wholesale_mwh": "sum",
        "delta_physical_mwh": "sum",
        "delta_bm_increase_mwh": "sum",
        "delta_bm_decrease_mwh": "sum",
    })
)

print()
print("=" * 90)
print("WIND: CHANGE FROM NO-ADDITIONAL-BESS BASELINE")
print("=" * 90)

print(
    wind_summary.to_string(
        index=False,
        formatters={
            "delta_wholesale_mwh": "{:,.2f}".format,
            "delta_physical_mwh": "{:,.2f}".format,
            "delta_bm_increase_mwh": "{:,.2f}".format,
            "delta_bm_decrease_mwh": "{:,.2f}".format,
        }
    )
)


# ============================================================
# 120 MW: WHICH CARRIERS CHANGED MOST?
# ============================================================

case120 = comparison[
    comparison["bess_mw"] == 120
].copy()

case120["absolute_bm_change"] = (
    case120["delta_bm_increase_mwh"].abs()
    + case120["delta_bm_decrease_mwh"].abs()
)

case120 = case120.sort_values(
    "absolute_bm_change",
    ascending=False
)

print()
print("=" * 90)
print("120 MW CASE - LARGEST CHANGES IN BM REDISPATCH BY CARRIER")
print("=" * 90)

print(
    case120[
        [
            "carrier",
            "delta_wholesale_mwh",
            "delta_physical_mwh",
            "delta_bm_increase_mwh",
            "delta_bm_decrease_mwh",
        ]
    ]
    .head(12)
    .to_string(
        index=False,
        formatters={
            "delta_wholesale_mwh": "{:,.2f}".format,
            "delta_physical_mwh": "{:,.2f}".format,
            "delta_bm_increase_mwh": "{:,.2f}".format,
            "delta_bm_decrease_mwh": "{:,.2f}".format,
        }
    )
)


# ============================================================
# FIGURE 1 - CCGT WHOLESALE VS PHYSICAL
# ============================================================

plt.figure(figsize=(9, 5.5))

plt.plot(
    ccgt_summary["bess_mw"],
    ccgt_summary["delta_wholesale_mwh"] / 1000,
    marker="o",
    label="Wholesale CCGT position",
)

plt.plot(
    ccgt_summary["bess_mw"],
    ccgt_summary["delta_physical_mwh"] / 1000,
    marker="o",
    label="Physical CCGT generation",
)

plt.plot(
    ccgt_summary["bess_mw"],
    ccgt_summary["delta_bm_increase_mwh"] / 1000,
    marker="o",
    label="CCGT BM upward redispatch",
)

plt.axhline(0, linestyle="--")

plt.xlabel("Additional BESS power at BEAT4- (MW)")
plt.ylabel("Change from baseline (GWh)")
plt.title("CCGT wholesale position versus network-constrained dispatch")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

ccgt_figure = FIGURES / "ccgt_wholesale_physical_gap.png"

plt.savefig(
    ccgt_figure,
    dpi=300,
    bbox_inches="tight",
)

plt.close()


# ============================================================
# FIGURE 2 - 120 MW CARRIER REDISPATCH CHANGE
# ============================================================

top120 = case120.head(8).copy()

x = range(len(top120))
width = 0.36

plt.figure(figsize=(10, 6))

plt.bar(
    [i - width / 2 for i in x],
    top120["delta_bm_increase_mwh"] / 1000,
    width=width,
    label="Change in BM increase",
)

plt.bar(
    [i + width / 2 for i in x],
    top120["delta_bm_decrease_mwh"] / 1000,
    width=width,
    label="Change in BM decrease",
)

plt.axhline(0, linestyle="--")

plt.xticks(
    list(x),
    top120["carrier"],
    rotation=35,
    ha="right",
)

plt.ylabel("Change from baseline (GWh)")
plt.title("120 MW BESS: change in redispatch by technology")
plt.legend()
plt.tight_layout()

carrier_figure = (
    FIGURES
    / "bess120_carrier_redispatch_change.png"
)

plt.savefig(
    carrier_figure,
    dpi=300,
    bbox_inches="tight",
)

plt.close()


print()
print("FIGURES SAVED")
print(ccgt_figure)
print(carrier_figure)

print()
print("=" * 90)
print("DIAGNOSTIC COMPLETE")
print("=" * 90)