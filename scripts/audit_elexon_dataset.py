from pathlib import Path
from datetime import date, timedelta

import pandas as pd


# ============================================================
# PATHS
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[2]

PROJECT_DIR = (
    REPO_ROOT
    / "project1_gb_market"
)

RAW_DIR = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "elexon"
)

PROCESSED_DIR = (
    PROJECT_DIR
    / "data"
    / "processed"
)

QA_DIR = (
    PROJECT_DIR
    / "results"
    / "data_quality"
)

QA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# YEARS
# ============================================================

START_YEAR = 2022
END_YEAR = 2025


# ============================================================
# EXPECTED BSC SETTLEMENT CALENDAR
# ============================================================

def build_expected_calendar(
    start_year,
    end_year
):

    rows = []

    current_date = date(
        start_year,
        1,
        1
    )

    final_date = date(
        end_year,
        12,
        31
    )

    while current_date <= final_date:

        next_date = (
            current_date
            + timedelta(days=1)
        )

        # Settlement Periods are based
        # on UK local time.
        #
        # Normal day = 48
        # Spring clock change = 46
        # Autumn clock change = 50

        start_local = pd.Timestamp(
            current_date
        ).tz_localize(
            "Europe/London"
        )

        end_local = pd.Timestamp(
            next_date
        ).tz_localize(
            "Europe/London"
        )

        duration = (
            end_local.tz_convert("UTC")
            -
            start_local.tz_convert("UTC")
        )

        number_of_periods = int(
            duration
            / pd.Timedelta(
                minutes=30
            )
        )

        for settlement_period in range(
            1,
            number_of_periods + 1
        ):

            rows.append(
                {
                    "settlementDate":
                        current_date,

                    "settlementPeriod":
                        settlement_period,

                    "expected_periods_that_day":
                        number_of_periods,

                    "year":
                        current_date.year
                }
            )

        current_date = next_date

    return pd.DataFrame(rows)


# ============================================================
# PREPARE DATASET KEYS
# ============================================================

def prepare_keys(df):

    df = df.copy()

    df["settlementDate"] = (
        pd.to_datetime(
            df["settlementDate"],
            errors="coerce"
        ).dt.date
    )

    df["settlementPeriod"] = (
        pd.to_numeric(
            df["settlementPeriod"],
            errors="coerce"
        )
    )

    df = df.dropna(
        subset=[
            "settlementDate",
            "settlementPeriod"
        ]
    )

    df["settlementPeriod"] = (
        df["settlementPeriod"]
        .astype(int)
    )

    return df


# ============================================================
# FIND MISSING PERIODS
# ============================================================

def find_missing_periods(
    expected,
    actual
):

    actual_keys = (
        actual[
            [
                "settlementDate",
                "settlementPeriod"
            ]
        ]
        .drop_duplicates()
    )

    merged = expected.merge(
        actual_keys,
        on=[
            "settlementDate",
            "settlementPeriod"
        ],
        how="left",
        indicator=True
    )

    missing = (
        merged[
            merged["_merge"]
            == "left_only"
        ]
        .drop(
            columns="_merge"
        )
        .reset_index(drop=True)
    )

    return missing


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 72
    )

    print(
        "PROJECT 1 - ELEXON DATA QUALITY AUDIT"
    )

    print(
        "=" * 72
    )


    # --------------------------------------------------------
    # EXPECTED SETTLEMENT CALENDAR
    # --------------------------------------------------------

    expected = build_expected_calendar(
        START_YEAR,
        END_YEAR
    )

    print(
        f"\nExpected settlement periods "
        f"2022-2025: {len(expected):,}"
    )

    print(
        "\nExpected periods by year:"
    )

    print(
        expected.groupby(
            "year"
        ).size()
    )


    # --------------------------------------------------------
    # COMBINED DATASET
    # --------------------------------------------------------

    combined_path = (
        PROCESSED_DIR
        / "gb_market_core_2022_2025.csv"
    )

    combined = pd.read_csv(
        combined_path
    )

    combined = prepare_keys(
        combined
    )

    print(
        f"\nCombined dataset rows: "
        f"{len(combined):,}"
    )


    # --------------------------------------------------------
    # COMPLETELY MISSING SETTLEMENT PERIODS
    # --------------------------------------------------------

    missing_master = (
        find_missing_periods(
            expected,
            combined
        )
    )

    print(
        "\nCompletely missing periods:"
    )

    print(
        len(missing_master)
    )

    if not missing_master.empty:

        print(
            missing_master[
                [
                    "settlementDate",
                    "settlementPeriod",
                    "year"
                ]
            ].to_string(
                index=False
            )
        )

    missing_master.to_csv(
        QA_DIR
        / "missing_master_periods.csv",
        index=False
    )


    # --------------------------------------------------------
    # MISSING DEMAND INSIDE MASTER DATASET
    # --------------------------------------------------------

    if "demand_mw" in combined.columns:

        missing_demand = combined[
            combined["demand_mw"].isna()
        ].copy()

        print(
            "\nRows with missing demand_mw:"
        )

        print(
            len(missing_demand)
        )

        if not missing_demand.empty:

            print(
                "\nMissing demand by year:"
            )

            print(
                missing_demand.groupby(
                    "year"
                ).size()
            )

            print(
                "\nFirst 30 missing "
                "demand periods:"
            )

            print(
                missing_demand[
                    [
                        "settlementDate",
                        "settlementPeriod",
                        "year"
                    ]
                ]
                .head(30)
                .to_string(
                    index=False
                )
            )

        missing_demand.to_csv(
            QA_DIR
            / "missing_demand_periods.csv",
            index=False
        )


    # --------------------------------------------------------
    # AUDIT RAW FUELHH
    # --------------------------------------------------------

    all_fuel_missing = []

    for year in range(
        START_YEAR,
        END_YEAR + 1
    ):

        fuel_path = (
            RAW_DIR
            / f"fuelhh_{year}.csv"
        )

        fuel = pd.read_csv(
            fuel_path
        )

        fuel = prepare_keys(
            fuel
        )

        expected_year = expected[
            expected["year"]
            == year
        ]

        missing_fuel = (
            find_missing_periods(
                expected_year,
                fuel
            )
        )

        missing_fuel[
            "dataset"
        ] = "FUELHH"

        all_fuel_missing.append(
            missing_fuel
        )

        print(
            f"\n{year} FUELHH missing "
            f"settlement periods: "
            f"{len(missing_fuel)}"
        )

        if not missing_fuel.empty:

            print(
                missing_fuel[
                    [
                        "settlementDate",
                        "settlementPeriod"
                    ]
                ].to_string(
                    index=False
                )
            )


    fuel_missing = pd.concat(
        all_fuel_missing,
        ignore_index=True
    )

    fuel_missing.to_csv(
        QA_DIR
        / "missing_fuelhh_periods.csv",
        index=False
    )


    # --------------------------------------------------------
    # AUDIT RAW INDO
    # --------------------------------------------------------

    all_indo_missing = []

    for year in range(
        START_YEAR,
        END_YEAR + 1
    ):

        indo_path = (
            RAW_DIR
            / f"indo_{year}.csv"
        )

        indo = pd.read_csv(
            indo_path
        )

        indo = prepare_keys(
            indo
        )

        expected_year = expected[
            expected["year"]
            == year
        ]

        missing_indo = (
            find_missing_periods(
                expected_year,
                indo
            )
        )

        missing_indo[
            "dataset"
        ] = "INDO"

        all_indo_missing.append(
            missing_indo
        )

        print(
            f"\n{year} INDO missing "
            f"settlement periods: "
            f"{len(missing_indo)}"
        )


    indo_missing = pd.concat(
        all_indo_missing,
        ignore_index=True
    )

    indo_missing.to_csv(
        QA_DIR
        / "missing_indo_periods.csv",
        index=False
    )


    # --------------------------------------------------------
    # CLOCK CHANGE CHECK
    # --------------------------------------------------------

    unusual_days = (
        expected[
            expected[
                "expected_periods_that_day"
            ] != 48
        ]
        [
            [
                "settlementDate",
                "expected_periods_that_day"
            ]
        ]
        .drop_duplicates()
    )

    print(
        "\nClock-change settlement days:"
    )

    print(
        unusual_days.to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 72
    )

    print(
        "AUDIT COMPLETE"
    )

    print(
        "=" * 72
    )

    print(
        "\nReports saved to:"
    )

    print(
        QA_DIR
    )


if __name__ == "__main__":
    main()