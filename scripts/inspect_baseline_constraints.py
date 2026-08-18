from pathlib import Path
import pandas as pd

# ============================================================
# PATHS
# ============================================================

# Standalone research repository.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Separate sibling PyPSA-GB repository.
REPO = PROJECT_ROOT.parent / "PyPSA-GB"

MARKET = REPO / "resources" / "market"

SCENARIO = "Validation_Jan2020_UniformNetworkBaseline"

congestion_path = (
    MARKET / f"{SCENARIO}_congestion.csv"
)

constraint_path = (
    MARKET / f"{SCENARIO}_constraint_costs.csv"
)

redispatch_path = (
    MARKET / f"{SCENARIO}_redispatch_summary.csv"
)


# ============================================================
# HELPER FUNCTION
# ============================================================

def inspect_file(path, name):

    print("\n")
    print("=" * 70)
    print(name)
    print("=" * 70)

    print("\nExpected file:")
    print(path)

    if not path.exists():
        print("\nERROR: File does not exist.")
        return

    df = pd.read_csv(path)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    for c in df.columns:
        print(" ", c)

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    numeric = df.select_dtypes(include="number")

    if not numeric.empty:
        print("\nNumeric summary:")
        print(
            numeric
            .describe()
            .T
            .to_string()
        )
    else:
        print("\nNo numeric columns found.")

    return df


# ============================================================
# INSPECT CONGESTION
# ============================================================

congestion = inspect_file(
    congestion_path,
    "CONGESTION"
)


# ============================================================
# INSPECT CONSTRAINT COSTS
# ============================================================

constraint_costs = inspect_file(
    constraint_path,
    "CONSTRAINT COSTS"
)


# ============================================================
# INSPECT REDISPATCH
# ============================================================

redispatch = inspect_file(
    redispatch_path,
    "REDISPATCH"
)


# ============================================================
# EXTRA QUICK DIAGNOSTICS
# ============================================================

print("\n")
print("=" * 70)
print("QUICK DIAGNOSTICS")
print("=" * 70)


# ------------------------------------------------------------
# Congestion
# ------------------------------------------------------------

if congestion is not None:

    print("\nCONGESTION COLUMN NAMES:")
    print(list(congestion.columns))

    # Try to identify likely useful columns automatically
    possible_hour_cols = [
        c for c in congestion.columns
        if "hour" in c.lower()
        or "binding" in c.lower()
        or "congestion" in c.lower()
    ]

    possible_component_cols = [
        c for c in congestion.columns
        if "component" in c.lower()
        or "line" in c.lower()
        or "name" in c.lower()
        or "branch" in c.lower()
    ]

    print("\nPossible congestion metric columns:")
    print(possible_hour_cols)

    print("\nPossible component/name columns:")
    print(possible_component_cols)

    if possible_hour_cols:
        col = possible_hour_cols[0]

        try:
            top = (
                congestion
                .sort_values(
                    col,
                    ascending=False
                )
                .head(20)
            )

            print(
                f"\nTop 20 congestion rows sorted by '{col}':"
            )

            print(
                top.to_string(index=False)
            )

        except Exception as exc:
            print(
                "\nCould not sort congestion data:",
                exc
            )


# ------------------------------------------------------------
# Constraint costs
# ------------------------------------------------------------

if constraint_costs is not None:

    print("\nCONSTRAINT COST COLUMN NAMES:")
    print(list(constraint_costs.columns))

    possible_cost_cols = [
        c for c in constraint_costs.columns
        if "cost" in c.lower()
    ]

    print("\nPossible cost columns:")
    print(possible_cost_cols)

    for col in possible_cost_cols:

        if pd.api.types.is_numeric_dtype(
            constraint_costs[col]
        ):

            try:
                top = (
                    constraint_costs
                    .sort_values(
                        col,
                        ascending=False
                    )
                    .head(20)
                )

                print(
                    f"\nTop 20 rows sorted by '{col}':"
                )

                print(
                    top.to_string(index=False)
                )

            except Exception as exc:
                print(
                    f"\nCould not sort by {col}:",
                    exc
                )


# ------------------------------------------------------------
# Redispatch
# ------------------------------------------------------------

if redispatch is not None:

    print("\nREDISPATCH COLUMN NAMES:")
    print(list(redispatch.columns))

    possible_redispatch_cols = [
        c for c in redispatch.columns
        if "redispatch" in c.lower()
        or "increase" in c.lower()
        or "decrease" in c.lower()
        or "volume" in c.lower()
        or "mwh" in c.lower()
    ]

    print("\nPossible redispatch metric columns:")
    print(possible_redispatch_cols)

    for col in possible_redispatch_cols:

        if pd.api.types.is_numeric_dtype(
            redispatch[col]
        ):

            try:
                top_positive = (
                    redispatch
                    .sort_values(
                        col,
                        ascending=False
                    )
                    .head(15)
                )

                top_negative = (
                    redispatch
                    .sort_values(
                        col,
                        ascending=True
                    )
                    .head(15)
                )

                print(
                    f"\nLargest positive values for '{col}':"
                )

                print(
                    top_positive.to_string(index=False)
                )

                print(
                    f"\nLargest negative values for '{col}':"
                )

                print(
                    top_negative.to_string(index=False)
                )

            except Exception as exc:
                print(
                    f"\nCould not analyse {col}:",
                    exc
                )


print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)
