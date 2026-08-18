from pathlib import Path
from datetime import date, timedelta
import time

import pandas as pd
import requests


# ============================================================
# PATHS
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]

PROJECT_DIR = REPO_ROOT

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

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

QA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

BASE_URL = (
    "https://data.elexon.co.uk/bmrs/api/v1"
)

YEARS = [
    2022,
    2023,
    2024,
    2025
]

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent":
        "PyPSA-GB Research Project"
    }
)


# ============================================================
# API REQUEST
# ============================================================

def request_json(
    endpoint,
    params,
    retries=4
):

    url = (
        f"{BASE_URL}{endpoint}"
    )

    for attempt in range(
        1,
        retries + 1
    ):

        try:

            response = SESSION.get(
                url,
                params=params,
                timeout=90
            )

            response.raise_for_status()

            payload = response.json()

            if isinstance(
                payload,
                dict
            ):

                data = payload.get(
                    "data",
                    payload
                )

            else:

                data = payload

            if data is None:
                data = []

            if isinstance(
                data,
                dict
            ):

                data = [data]

            return data

        except Exception as exc:

            print(
                f"Request failed "
                f"{attempt}/{retries}: "
                f"{exc}"
            )

            if attempt == retries:
                raise

            time.sleep(
                2 ** attempt
            )


# ============================================================
# EXPECTED BSC SETTLEMENT CALENDAR
# ============================================================

def build_expected_calendar():

    rows = []

    current = date(
        2022,
        1,
        1
    )

    end = date(
        2025,
        12,
        31
    )

    while current <= end:

        next_day = (
            current
            + timedelta(days=1)
        )

        start_local = (
            pd.Timestamp(
                current
            )
            .tz_localize(
                "Europe/London"
            )
        )

        end_local = (
            pd.Timestamp(
                next_day
            )
            .tz_localize(
                "Europe/London"
            )
        )

        duration = (
            end_local.tz_convert("UTC")
            -
            start_local.tz_convert("UTC")
        )

        number_periods = int(
            duration
            / pd.Timedelta(
                minutes=30
            )
        )

        for sp in range(
            1,
            number_periods + 1
        ):

            rows.append(
                {
                    "settlementDate":
                        current,

                    "settlementPeriod":
                        sp,

                    "year":
                        current.year
                }
            )

        current = next_day

    return pd.DataFrame(
        rows
    )


# ============================================================
# STANDARDISE KEYS
# ============================================================

def prepare_keys(df):

    df = df.copy()

    df["settlementDate"] = (
        pd.to_datetime(
            df["settlementDate"],
            errors="coerce"
        )
        .dt.date
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

    for column in [
        "publishTime",
        "startTime"
    ]:

        if column in df.columns:

            df[column] = (
                pd.to_datetime(
                    df[column],
                    errors="coerce",
                    utc=True
                )
            )

    return df


# ============================================================
# FIND MISSING EXPECTED PERIODS
# ============================================================

def find_missing(
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

    return (
        merged[
            merged["_merge"]
            == "left_only"
        ]
        .drop(
            columns="_merge"
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# FIND UNEXPECTED PERIODS
# ============================================================

def find_unexpected(
    expected,
    actual
):

    expected_keys = (
        expected[
            [
                "settlementDate",
                "settlementPeriod"
            ]
        ]
        .drop_duplicates()
    )

    actual_keys = (
        actual[
            [
                "settlementDate",
                "settlementPeriod"
            ]
        ]
        .drop_duplicates()
    )

    merged = actual_keys.merge(
        expected_keys,
        on=[
            "settlementDate",
            "settlementPeriod"
        ],
        how="left",
        indicator=True
    )

    return (
        merged[
            merged["_merge"]
            == "left_only"
        ]
        .drop(
            columns="_merge"
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# REPAIR INDO
# ============================================================

def repair_indo(
    year,
    expected_year
):

    path = (
        RAW_DIR
        / f"indo_{year}.csv"
    )

    df = pd.read_csv(
        path
    )

    df = prepare_keys(
        df
    )

    missing = find_missing(
        expected_year,
        df
    )

    print(
        f"\n{year} INDO:"
        f" {len(missing)} "
        f"periods need recovery"
    )

    recovered_rows = []

    # Group by settlement date so we do not
    # make one request per individual SP.
    missing_dates = (
        missing[
            "settlementDate"
        ]
        .drop_duplicates()
        .tolist()
    )

    for number, settlement_date in enumerate(
        missing_dates,
        start=1
    ):

        print(
            f"  INDO repair "
            f"{number}/"
            f"{len(missing_dates)}: "
            f"{settlement_date}"
        )

        # Important:
        # settlement dates are UK local time,
        # while API filters are publish UTC.
        #
        # Pull a deliberately padded window
        # around the settlement date.
        day_before = (
            settlement_date
            - timedelta(days=1)
        )

        day_after = (
            settlement_date
            + timedelta(days=1)
        )

        params = {
            "publishDateTimeFrom":
                (
                    f"{day_before}"
                    f"T20:00:00Z"
                ),

            "publishDateTimeTo":
                (
                    f"{day_after}"
                    f"T04:00:00Z"
                ),

            "format":
                "json"
        }

        rows = request_json(
            "/datasets/INDO",
            params
        )

        candidate = (
            pd.json_normalize(
                rows
            )
        )

        if candidate.empty:
            continue

        candidate = prepare_keys(
            candidate
        )

        candidate = candidate[
            candidate[
                "settlementDate"
            ]
            == settlement_date
        ]

        recovered_rows.append(
            candidate
        )

        time.sleep(0.15)


    if recovered_rows:

        recovered = pd.concat(
            recovered_rows,
            ignore_index=True
        )

        df = pd.concat(
            [
                df,
                recovered
            ],
            ignore_index=True
        )


    # Latest publication per period
    if "publishTime" in df.columns:

        df = df.sort_values(
            "publishTime"
        )

    df = (
        df
        .drop_duplicates(
            subset=[
                "settlementDate",
                "settlementPeriod"
            ],
            keep="last"
        )
        .reset_index(drop=True)
    )

    # Keep raw recovered data.
    df.to_csv(
        path,
        index=False
    )

    remaining = find_missing(
        expected_year,
        df
    )

    print(
        f"  Remaining INDO gaps: "
        f"{len(remaining)}"
    )

    return (
        df,
        remaining
    )


# ============================================================
# REPAIR FUELHH
# ============================================================

def repair_fuelhh(
    year,
    expected_year
):

    path = (
        RAW_DIR
        / f"fuelhh_{year}.csv"
    )

    df = pd.read_csv(
        path
    )

    df = prepare_keys(
        df
    )

    missing = find_missing(
        expected_year,
        df
    )

    print(
        f"\n{year} FUELHH:"
        f" {len(missing)} "
        f"periods need recovery"
    )

    recovered_rows = []

    for number, row in enumerate(
        missing.itertuples(),
        start=1
    ):

        settlement_date = (
            row.settlementDate
        )

        sp = (
            row.settlementPeriod
        )

        print(
            f"  FUELHH repair "
            f"{number}/"
            f"{len(missing)}: "
            f"{settlement_date} "
            f"SP{sp}"
        )

        params = {
            "settlementDateFrom":
                settlement_date.isoformat(),

            "settlementDateTo":
                settlement_date.isoformat(),

            "settlementPeriod":
                sp,

            "format":
                "json"
        }

        rows = request_json(
            "/datasets/FUELHH",
            params
        )

        candidate = (
            pd.json_normalize(
                rows
            )
        )

        if candidate.empty:

            print(
                "    No API records returned"
            )

            continue

        candidate = prepare_keys(
            candidate
        )

        candidate = candidate[
            (
                candidate[
                    "settlementDate"
                ]
                == settlement_date
            )
            &
            (
                candidate[
                    "settlementPeriod"
                ]
                == sp
            )
        ]

        recovered_rows.append(
            candidate
        )

        time.sleep(0.15)


    if recovered_rows:

        recovered = pd.concat(
            recovered_rows,
            ignore_index=True
        )

        df = pd.concat(
            [
                df,
                recovered
            ],
            ignore_index=True
        )


    # One record per period / fuel type.
    if "publishTime" in df.columns:

        df = df.sort_values(
            "publishTime"
        )

    df = (
        df
        .drop_duplicates(
            subset=[
                "settlementDate",
                "settlementPeriod",
                "fuelType"
            ],
            keep="last"
        )
        .reset_index(drop=True)
    )

    df.to_csv(
        path,
        index=False
    )

    remaining = find_missing(
        expected_year,
        df
    )

    print(
        f"  Remaining FUELHH gaps: "
        f"{len(remaining)}"
    )

    return (
        df,
        remaining
    )


# ============================================================
# BUILD GENERATION TABLE
# ============================================================

def build_generation_wide(
    fuel
):

    wide = (
        fuel.pivot_table(
            index=[
                "settlementDate",
                "settlementPeriod"
            ],
            columns="fuelType",
            values="generation",
            aggfunc="last"
        )
        .reset_index()
    )

    wide.columns.name = None

    rename_map = {}

    for column in wide.columns:

        if column not in [
            "settlementDate",
            "settlementPeriod"
        ]:

            rename_map[column] = (
                "generation_"
                + str(column).lower()
                + "_mw"
            )

    return wide.rename(
        columns=rename_map
    )


# ============================================================
# REBUILD CLEAN MASTER
# ============================================================

def rebuild_master(
    expected,
    yearly_indo,
    yearly_fuel
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "REBUILDING CLEAN "
        "2022-2025 MASTER DATASET"
    )

    print(
        "=" * 70
    )

    all_years = []

    for year in YEARS:

        calendar = (
            expected[
                expected["year"]
                == year
            ]
            .copy()
        )

        indo = (
            yearly_indo[
                year
            ]
        )

        fuel = (
            yearly_fuel[
                year
            ]
        )


        # -----------------------------
        # Demand
        # -----------------------------

        demand_columns = [
            "settlementDate",
            "settlementPeriod",
            "demand"
        ]

        if "startTime" in indo.columns:

            demand_columns.append(
                "startTime"
            )

        demand = (
            indo[
                demand_columns
            ]
            .copy()
        )

        rename = {
            "demand":
                "demand_mw"
        }

        if (
            "startTime"
            in demand.columns
        ):

            rename[
                "startTime"
            ] = "timestamp_utc"

        demand = demand.rename(
            columns=rename
        )


        # -----------------------------
        # Generation
        # -----------------------------

        generation = (
            build_generation_wide(
                fuel
            )
        )


        # -----------------------------
        # IMPORTANT:
        # Expected BSC calendar is the
        # authoritative model index.
        # -----------------------------

        master = (
            calendar[
                [
                    "settlementDate",
                    "settlementPeriod",
                    "year"
                ]
            ]
            .merge(
                demand,
                on=[
                    "settlementDate",
                    "settlementPeriod"
                ],
                how="left",
                validate="one_to_one"
            )
            .merge(
                generation,
                on=[
                    "settlementDate",
                    "settlementPeriod"
                ],
                how="left",
                validate="one_to_one"
            )
        )

        year_path = (
            PROCESSED_DIR
            / f"gb_market_core_{year}.csv"
        )

        master.to_csv(
            year_path,
            index=False
        )

        all_years.append(
            master
        )


    combined = pd.concat(
        all_years,
        ignore_index=True
    )

    final_path = (
        PROCESSED_DIR
        / "gb_market_core_2022_2025.csv"
    )

    combined.to_csv(
        final_path,
        index=False
    )


    # -----------------------------
    # Final QA
    # -----------------------------

    print(
        f"\nFinal master rows: "
        f"{len(combined):,}"
    )

    print(
        f"Expected rows: "
        f"{len(expected):,}"
    )

    missing_demand = int(
        combined[
            "demand_mw"
        ]
        .isna()
        .sum()
    )

    generation_columns = [
        c
        for c in combined.columns
        if c.startswith(
            "generation_"
        )
    ]

    no_generation = int(
        combined[
            generation_columns
        ]
        .isna()
        .all(axis=1)
        .sum()
    )

    print(
        f"Missing demand rows: "
        f"{missing_demand}"
    )

    print(
        f"Rows with no generation "
        f"data: {no_generation}"
    )

    print(
        f"\nSaved clean master:"
        f"\n{final_path}"
    )

    return combined


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "PROJECT 1 - "
        "ELEXON GAP REPAIR"
    )

    print(
        "=" * 70
    )

    expected = (
        build_expected_calendar()
    )

    yearly_indo = {}
    yearly_fuel = {}

    unresolved_indo = []
    unresolved_fuel = []


    # ========================================================
    # TARGETED REPAIR
    # ========================================================

    for year in YEARS:

        expected_year = (
            expected[
                expected["year"]
                == year
            ]
        )


        indo, indo_missing = (
            repair_indo(
                year,
                expected_year
            )
        )

        fuel, fuel_missing = (
            repair_fuelhh(
                year,
                expected_year
            )
        )

        yearly_indo[
            year
        ] = indo

        yearly_fuel[
            year
        ] = fuel


        if not indo_missing.empty:

            unresolved_indo.append(
                indo_missing
            )

        if not fuel_missing.empty:

            unresolved_fuel.append(
                fuel_missing
            )


    # ========================================================
    # CHECK UNEXPECTED RAW KEYS
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "CHECKING UNEXPECTED "
        "SETTLEMENT KEYS"
    )

    print(
        "=" * 70
    )

    unexpected_all = []

    for year in YEARS:

        expected_year = (
            expected[
                expected["year"]
                == year
            ]
        )

        unexpected = (
            find_unexpected(
                expected_year,
                yearly_fuel[
                    year
                ]
            )
        )

        if not unexpected.empty:

            unexpected[
                "year"
            ] = year

            unexpected_all.append(
                unexpected
            )

            print(
                f"\n{year} unexpected "
                f"FUELHH periods:"
            )

            print(
                unexpected.to_string(
                    index=False
                )
            )


    if unexpected_all:

        unexpected_df = (
            pd.concat(
                unexpected_all,
                ignore_index=True
            )
        )

        unexpected_df.to_csv(
            QA_DIR
            / "unexpected_fuelhh_periods.csv",
            index=False
        )


    # ========================================================
    # REBUILD MASTER
    # ========================================================

    rebuild_master(
        expected,
        yearly_indo,
        yearly_fuel
    )


    # ========================================================
    # SAVE UNRESOLVED GAPS
    # ========================================================

    if unresolved_indo:

        pd.concat(
            unresolved_indo,
            ignore_index=True
        ).to_csv(
            QA_DIR
            / "unresolved_indo_after_repair.csv",
            index=False
        )


    if unresolved_fuel:

        pd.concat(
            unresolved_fuel,
            ignore_index=True
        ).to_csv(
            QA_DIR
            / "unresolved_fuelhh_after_repair.csv",
            index=False
        )


    print(
        "\n"
        + "=" * 70
    )

    print(
        "ELEXON GAP REPAIR COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()