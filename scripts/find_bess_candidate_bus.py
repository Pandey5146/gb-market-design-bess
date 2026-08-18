from pathlib import Path

import pandas as pd
import pypsa


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPO = PROJECT_ROOT.parent / "PyPSA-GB"

SCENARIO = "Validation_Jan2020_UniformNetworkBaseline"

NETWORK_PATH = (
    REPO
    / "resources"
    / "network"
    / f"{SCENARIO}.nc"
)

REDISPATCH_PATH = (
    REPO
    / "resources"
    / "market"
    / f"{SCENARIO}_redispatch_summary.csv"
)

CONGESTION_PATH = (
    REPO
    / "resources"
    / "market"
    / f"{SCENARIO}_congestion.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("LOADING NETWORK")
print("=" * 80)

n = pypsa.Network(NETWORK_PATH)

redispatch = pd.read_csv(REDISPATCH_PATH)
congestion = pd.read_csv(CONGESTION_PATH)

print("\nNetwork loaded:")
print("Buses:", len(n.buses))
print("Generators:", len(n.generators))
print("Storage units:", len(n.storage_units))
print("Lines:", len(n.lines))


# ============================================================
# TOP DOWNWARD REDISPATCH GENERATORS
# ============================================================

down = redispatch[
    redispatch["type"].eq("generator")
].copy()

down = down.sort_values(
    "decrease_MWh",
    ascending=False
)

top_down = down.head(30).copy()


# ============================================================
# MAP GENERATORS TO BUSES
# ============================================================

generator_bus = n.generators["bus"].to_dict()

top_down["bus"] = (
    top_down["component"]
    .map(generator_bus)
)


# Add bus coordinates if available

if "x" in n.buses.columns:
    top_down["bus_x"] = (
        top_down["bus"]
        .map(n.buses["x"])
    )

if "y" in n.buses.columns:
    top_down["bus_y"] = (
        top_down["bus"]
        .map(n.buses["y"])
    )


print("\n")
print("=" * 80)
print("TOP 30 DOWNWARD REDISPATCH GENERATORS")
print("=" * 80)

columns = [
    "component",
    "carrier",
    "decrease_MWh",
    "increase_MWh",
    "net_cost",
    "bus",
]

if "bus_x" in top_down.columns:
    columns += ["bus_x", "bus_y"]

print(
    top_down[columns]
    .to_string(index=False)
)


# ============================================================
# AGGREGATE DOWNWARD REDISPATCH BY BUS
# ============================================================

mapped = redispatch[
    redispatch["type"].eq("generator")
].copy()

mapped["bus"] = (
    mapped["component"]
    .map(generator_bus)
)

bus_redispatch = (
    mapped
    .dropna(subset=["bus"])
    .groupby("bus")
    .agg(
        decrease_MWh=("decrease_MWh", "sum"),
        increase_MWh=("increase_MWh", "sum"),
        net_cost=("net_cost", "sum"),
    )
    .reset_index()
)

bus_redispatch["net_down_MWh"] = (
    bus_redispatch["decrease_MWh"]
    - bus_redispatch["increase_MWh"]
)

bus_redispatch = (
    bus_redispatch
    .sort_values(
        "net_down_MWh",
        ascending=False
    )
)


# Add coordinates

if "x" in n.buses.columns:
    bus_redispatch["x"] = (
        bus_redispatch["bus"]
        .map(n.buses["x"])
    )

if "y" in n.buses.columns:
    bus_redispatch["y"] = (
        bus_redispatch["bus"]
        .map(n.buses["y"])
    )


print("\n")
print("=" * 80)
print("TOP 25 BUSES BY NET DOWNWARD REDISPATCH")
print("=" * 80)

print(
    bus_redispatch
    .head(25)
    .to_string(index=False)
)


# ============================================================
# INSPECT TOP CONGESTED LINES AND THEIR END BUSES
# ============================================================

print("\n")
print("=" * 80)
print("TOP CONGESTED LINES + BUS CONNECTIONS")
print("=" * 80)

top_lines = (
    congestion
    .sort_values(
        "hours_congested",
        ascending=False
    )
    .head(20)
    .copy()
)

line_bus0 = n.lines["bus0"].to_dict()
line_bus1 = n.lines["bus1"].to_dict()

top_lines["bus0"] = (
    top_lines["component"]
    .map(line_bus0)
)

top_lines["bus1"] = (
    top_lines["component"]
    .map(line_bus1)
)

print(
    top_lines[
        [
            "component",
            "s_nom_MVA",
            "max_loading_fraction",
            "hours_congested",
            "mean_loading_fraction",
            "bus0",
            "bus1",
        ]
    ]
    .to_string(index=False)
)


# ============================================================
# EXISTING STORAGE BY BUS
# ============================================================

print("\n")
print("=" * 80)
print("EXISTING STORAGE")
print("=" * 80)

storage_cols = [
    c for c in
    [
        "bus",
        "carrier",
        "p_nom",
        "max_hours",
    ]
    if c in n.storage_units.columns
]

storage = (
    n.storage_units[storage_cols]
    .copy()
)

storage["name"] = storage.index

storage = storage[
    ["name"] + storage_cols
]

print(
    storage
    .sort_values(
        "p_nom",
        ascending=False
    )
    .head(30)
    .to_string(index=False)
)


# ============================================================
# SAVE CANDIDATE TABLE
# ============================================================

OUTPUT = (
    PROJECT_ROOT
    / "results"
    / "bess_candidate_buses.csv"
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

bus_redispatch.to_csv(
    OUTPUT,
    index=False
)

print("\nSaved:")
print(OUTPUT)

print("\nDONE")