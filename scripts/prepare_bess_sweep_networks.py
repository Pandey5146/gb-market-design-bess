from pathlib import Path
import math

import pypsa


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPO = PROJECT_ROOT.parent / "PyPSA-GB"

BASE_SCENARIO = "Validation_Jan2020_UniformNetworkBaseline"

BASE_NETWORK = (
    REPO
    / "resources"
    / "network"
    / f"{BASE_SCENARIO}.nc"
)

BESS_BUS = "BEAT4-"

# Additional battery capacity scenarios
BESS_SIZES_MW = [50, 70, 100, 120]

DURATION_H = 2.0

# PyPSA-GB Battery defaults:
# 90% round-trip efficiency, symmetric charge/discharge
ROUND_TRIP_EFFICIENCY = 0.90
ETA = math.sqrt(ROUND_TRIP_EFFICIENCY)

STANDING_LOSS = 0.001
MARGINAL_COST = 0.1

# Fixed capacity, therefore capital cost does not affect dispatch optimisation
CAPITAL_COST = 400.0

INITIAL_SOC_FRACTION = 0.50


# ============================================================
# CHECK BASELINE
# ============================================================

print("=" * 80)
print("BESS POWER-SIZE SWEEP")
print("=" * 80)

print("\nBaseline network:")
print(BASE_NETWORK)

if not BASE_NETWORK.exists():
    raise FileNotFoundError(
        f"Baseline network not found:\n{BASE_NETWORK}"
    )

base = pypsa.Network(BASE_NETWORK)

print("\nBaseline loaded successfully.")
print("Buses:", len(base.buses))
print("Generators:", len(base.generators))
print("Storage units:", len(base.storage_units))

if BESS_BUS not in base.buses.index:
    raise ValueError(
        f"Selected BESS bus '{BESS_BUS}' does not exist."
    )

print(f"\nSelected BESS bus exists: {BESS_BUS}")


# ============================================================
# EXISTING BATTERY CAPACITY
# ============================================================

existing_batteries = base.storage_units[
    base.storage_units["carrier"].astype(str).str.lower() == "battery"
].copy()

existing_battery_power = existing_batteries["p_nom"].sum()

existing_battery_energy = (
    existing_batteries["p_nom"]
    * existing_batteries["max_hours"]
).sum()

print("\nExisting baseline batteries:")
print(f"Units: {len(existing_batteries)}")
print(f"Power: {existing_battery_power:.2f} MW")
print(f"Energy: {existing_battery_energy:.2f} MWh")


# ============================================================
# CREATE COUNTERFACTUAL NETWORKS
# ============================================================

created = []

for power_mw in BESS_SIZES_MW:

    scenario = (
        f"Research_Jan2020_BEAT4_BESS{power_mw}"
    )

    bess_name = (
        f"Research_BESS_BEAT4_{power_mw}MW"
    )

    output_path = (
        REPO
        / "resources"
        / "network"
        / f"{scenario}.nc"
    )

    print("\n")
    print("=" * 80)
    print(f"CREATING {scenario}")
    print("=" * 80)

    # Fresh copy of original baseline for every experiment
    n = pypsa.Network(BASE_NETWORK)

    energy_mwh = power_mw * DURATION_H
    initial_soc_mwh = energy_mwh * INITIAL_SOC_FRACTION

    # Safety check
    if bess_name in n.storage_units.index:
        n.remove(
            "StorageUnit",
            bess_name
        )

    n.add(
        "StorageUnit",
        bess_name,

        bus=BESS_BUS,

        carrier="Battery",

        p_nom=float(power_mw),

        p_nom_extendable=False,

        max_hours=DURATION_H,

        efficiency_store=ETA,

        efficiency_dispatch=ETA,

        standing_loss=STANDING_LOSS,

        marginal_cost=MARGINAL_COST,

        capital_cost=CAPITAL_COST,

        state_of_charge_initial=initial_soc_mwh,

        cyclic_state_of_charge=False,
    )

    # ========================================================
    # QA
    # ========================================================

    row = n.storage_units.loc[bess_name]

    print("\nAdded battery:")
    print("Name:", bess_name)
    print("Bus:", row["bus"])
    print("Power:", row["p_nom"], "MW")
    print(
        "Energy:",
        row["p_nom"] * row["max_hours"],
        "MWh",
    )
    print("Duration:", row["max_hours"], "h")
    print(
        "Charge efficiency:",
        row["efficiency_store"],
    )
    print(
        "Discharge efficiency:",
        row["efficiency_dispatch"],
    )
    print(
        "Initial SOC:",
        row["state_of_charge_initial"],
        "MWh",
    )

    total_battery_power = n.storage_units.loc[
        n.storage_units["carrier"]
        .astype(str)
        .str.lower()
        .eq("battery"),
        "p_nom",
    ].sum()

    print(
        "Total system battery power after addition:",
        f"{total_battery_power:.2f} MW",
    )

    # ========================================================
    # SAVE
    # ========================================================

    n.export_to_netcdf(output_path)

    print("\nSaved:")
    print(output_path)

    created.append(
        {
            "scenario": scenario,
            "bess_mw": power_mw,
            "bess_mwh": energy_mwh,
            "output": output_path,
        }
    )


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("=" * 80)
print("BESS SWEEP NETWORKS CREATED")
print("=" * 80)

print("\nBaseline:")
print("0 MW additional BESS")

for item in created:
    print(
        f"{item['bess_mw']:>3} MW"
        f" / {item['bess_mwh']:>3.0f} MWh"
        f" -> {item['scenario']}"
    )

print("\nExperimental design:")
print("0 / 50 / 70 / 100 / 120 MW")
print("All batteries = 2-hour duration")
print(f"Location = {BESS_BUS}")
print("Baseline network has NOT been modified.")

print("\nDONE")