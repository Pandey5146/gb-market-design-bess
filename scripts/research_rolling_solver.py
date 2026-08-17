from pathlib import Path
import argparse
import logging
import sys

import pandas as pd
import pypsa
import yaml


# ============================================================
# PATHS
# ============================================================

# research_rolling_solver.py is located at:
# PyPSA-GB/project1_gb_market/scripts/
REPO_ROOT = Path(__file__).resolve().parents[2]

# Make the main PyPSA-GB repository importable
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# IMPORT PYPSA-GB'S EXISTING SOLVE FUNCTIONS
# ============================================================

from scripts.solve.solve_network import (
    validate_network_costs,
    apply_transmission_relaxation,
    apply_line_rating_overrides,
    apply_outage_schedule,
    improve_numerical_conditioning,
    apply_load_shedding_limits,
    configure_solver,
    build_hydro_constraints_callback,
    _build_neso_boundary_constraints_callback,
    combine_extra_functionalities,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("research_rolling_solver")


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

parser = argparse.ArgumentParser(
    description="Rolling-horizon solver for PyPSA-GB research scenarios"
)

parser.add_argument(
    "--scenario",
    required=True,
    help="Scenario name from config/scenarios.yaml",
)

parser.add_argument(
    "--horizon",
    type=int,
    default=336,
    help="Rolling optimisation horizon in hours",
)

parser.add_argument(
    "--overlap",
    type=int,
    default=168,
    help="Overlap between rolling horizons in hours",
)

args = parser.parse_args()


SCENARIO = args.scenario
HORIZON = args.horizon
OVERLAP = args.overlap


# ============================================================
# LOAD CONFIGURATION
# ============================================================

scenarios_file = REPO_ROOT / "config" / "scenarios.yaml"
main_config_file = REPO_ROOT / "config" / "config.yaml"

with open(scenarios_file, "r", encoding="utf-8") as f:
    scenarios = yaml.safe_load(f)

with open(main_config_file, "r", encoding="utf-8") as f:
    main_config = yaml.safe_load(f)


if SCENARIO not in scenarios:
    raise KeyError(
        f"Scenario '{SCENARIO}' not found in {scenarios_file}"
    )

scenario_config = scenarios[SCENARIO]


# ============================================================
# INPUT / OUTPUT FILES
# ============================================================

network_file = (
    REPO_ROOT
    / "resources"
    / "network"
    / f"{SCENARIO}.nc"
)

output_file = (
    REPO_ROOT
    / "resources"
    / "network"
    / f"{SCENARIO}_rolling_solved.nc"
)


if not network_file.exists():
    raise FileNotFoundError(
        f"\nPrepared network does not exist:\n{network_file}\n\n"
        "Run the scenario through Snakemake first so PyPSA-GB "
        "can construct the network."
    )


# ============================================================
# LOAD NETWORK
# ============================================================

logger.info("=" * 70)
logger.info("PYPSA-GB RESEARCH ROLLING-HORIZON SOLVER")
logger.info("=" * 70)

logger.info("Scenario: %s", SCENARIO)
logger.info("Input network: %s", network_file)
logger.info("Horizon: %s hours", HORIZON)
logger.info("Overlap: %s hours", OVERLAP)

network = pypsa.Network(network_file)

logger.info(
    "Loaded network with %s snapshots",
    len(network.snapshots),
)


# ============================================================
# SAME PREPROCESSING USED BY PYPSA-GB
# ============================================================

logger.info("Applying PyPSA-GB preprocessing...")

validate_network_costs(
    network,
    logger,
)

apply_transmission_relaxation(
    network,
    scenario_config,
    logger,
)

apply_line_rating_overrides(
    network,
    scenario_config,
    logger,
)

apply_outage_schedule(
    network,
    scenario_config,
    logger,
)

improve_numerical_conditioning(
    network,
    logger,
)


# ============================================================
# SELECT THE SCENARIO SOLVE PERIOD
# ============================================================

solve_period = scenario_config.get("solve_period", {})

if solve_period.get("enabled", False):

    start = pd.Timestamp(
        solve_period["start"]
    )

    end = pd.Timestamp(
        solve_period["end"]
    )

    selected_snapshots = network.snapshots[
        (network.snapshots >= start)
        & (network.snapshots <= end)
    ]

    if len(selected_snapshots) == 0:
        raise ValueError(
            f"No snapshots found between {start} and {end}"
        )

    network.set_snapshots(
        selected_snapshots
    )


logger.info(
    "Solve snapshots: %s",
    len(network.snapshots),
)

logger.info(
    "Solve start: %s",
    network.snapshots[0],
)

logger.info(
    "Solve end: %s",
    network.snapshots[-1],
)


# ============================================================
# LOAD SHEDDING CONTROLS
# ============================================================

apply_load_shedding_limits(
    network,
    logger,
)


# ============================================================
# SOLVER CONFIGURATION
# ============================================================

solver_config = main_config.get(
    "solver",
    {},
)

solver_name = solver_config.get(
    "name",
    "highs",
)

solver_options = solver_config.get(
    "options",
    {},
).copy()


# Ensure settings suitable for this machine
solver_options.setdefault(
    "threads",
    4,
)

solver_options.setdefault(
    "log_to_console",
    False,
)


solver_name, solver_options = configure_solver(
    network,
    solver_name,
    solver_options,
    logger,
)


logger.info(
    "Solver: %s",
    solver_name,
)

logger.info(
    "Solver options: %s",
    solver_options,
)


# ============================================================
# PYPSA-GB CUSTOM CONSTRAINTS
# ============================================================

logger.info(
    "Building PyPSA-GB hydro constraints..."
)

hydro_callback = (
    build_hydro_constraints_callback(
        network,
        scenario_config,
    )
)


logger.info(
    "Building NESO boundary constraints..."
)

neso_callback = (
    _build_neso_boundary_constraints_callback(
        network,
        scenario_config,
        logger,
    )
)


extra_functionality = (
    combine_extra_functionalities(
        hydro_callback,
        neso_callback,
    )
)


# ============================================================
# ROLLING-HORIZON OPTIMISATION
# ============================================================

logger.info("=" * 70)
logger.info("STARTING ROLLING-HORIZON OPTIMISATION")
logger.info("=" * 70)

logger.info(
    "Horizon = %s hours | Overlap = %s hours",
    HORIZON,
    OVERLAP,
)


network.optimize.optimize_with_rolling_horizon(
    snapshots=network.snapshots,
    horizon=HORIZON,
    overlap=OVERLAP,
    solver_name=solver_name,
    solver_options=solver_options,
    extra_functionality=extra_functionality,
)


# ============================================================
# SAVE SOLVED NETWORK
# ============================================================

logger.info("=" * 70)
logger.info("ROLLING OPTIMISATION COMPLETE")
logger.info("=" * 70)

logger.info(
    "Saving solved network to:\n%s",
    output_file,
)

network.export_to_netcdf(
    output_file
)

logger.info(
    "Saved successfully."
)

logger.info(
    "Snapshots solved: %s",
    len(network.snapshots),
)

logger.info(
    "Start: %s",
    network.snapshots[0],
)

logger.info(
    "End: %s",
    network.snapshots[-1],
)

logger.info("=" * 70)