from pathlib import Path
from datetime import date, timedelta
import time

import pandas as pd
import requests


# ============================================================
# PROJECT SETTINGS
# ============================================================

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

START_YEAR = 2022
END_YEAR = 2025

CHUNK_DAYS = 7

REPO_ROOT = Path(__file__).resolve().parents[2]

PROJECT_DIR = REPO_ROOT / "project1_gb_market"

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

RAW_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent":
        "PyPSA-GB Research Project / "
        "Historical GB Market Analysis"
    }
)


# ============================================================
# GENERIC ELEXON API REQUEST
# ============================================================

def request_json(
    endpoint,
    params,
    retries=4
):

    url = f"{BASE_URL}{endpoint}"

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
                f"\nRequest failed "
                f"(attempt {attempt}/"
                f"{retries})"
            )

            print(exc)

            if attempt == retries:
                raise

            wait_seconds = (
                2 ** attempt
            )

            print(
                f"Waiting "
                f"{wait_seconds}s..."
            )

            time.sleep(
                wait_seconds
            )


# ============================================================
# DATE CHUNKS
# ============================================================

def make_date_chunks(
    start_date,
    end_date,
    days=7
):

    current = start_date

    while current <= end_date:

        chunk_end = min(
            current
            + timedelta(
                days=days - 1
            ),
            end_date
        )

        yield (
            current,
            chunk_end
        )

        current = (
            chunk_end
            + timedelta(days=1)
        )


# ============================================================
# FILTER TO REQUESTED SETTLEMENT DATES
# ============================================================

def filter_settlement_dates(
    df,
    start_date,
    end_date
):

    if df.empty:
        return df

    if (
        "settlementDate"
        not in df.columns
    ):
        return df

    df["settlementDate"] = (
        pd.to_datetime(
            df["settlementDate"],
            errors="coerce"
        ).dt.date
    )

    mask = (
        (
            df["settlementDate"]
            >= start_date
        )
        &
        (
            df["settlementDate"]
            <= end_date
        )
    )

    return (
        df.loc[mask]
        .copy()
        .reset_index(drop=True)
    )


# ============================================================
# BASIC CLEANING
# ============================================================

def clean_dataframe(df):

    if df.empty:
        return df

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

    df = (
        df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return df


# ============================================================
# DOWNLOAD FUELHH
# ============================================================

def fetch_fuelhh(
    start_date,
    end_date
):

    all_rows = []

    chunks = list(
        make_date_chunks(
            start_date,
            end_date,
            CHUNK_DAYS
        )
    )

    for number, (
        chunk_start,
        chunk_end
    ) in enumerate(
        chunks,
        start=1
    ):

        print(
            f"  FUELHH "
            f"{number}/{len(chunks)}: "
            f"{chunk_start} -> "
            f"{chunk_end}"
        )

        # Request one extra calendar day.
        # We filter back to the exact
        # settlement-date interval afterwards.
        request_end = (
            chunk_end
            + timedelta(days=1)
        )

        params = {
            "settlementDateFrom":
                chunk_start.isoformat(),

            "settlementDateTo":
                request_end.isoformat(),

            "format":
                "json"
        }

        rows = request_json(
            "/datasets/FUELHH",
            params
        )

        chunk_df = (
            pd.json_normalize(
                rows
            )
        )

        chunk_df = (
            filter_settlement_dates(
                chunk_df,
                chunk_start,
                chunk_end
            )
        )

        all_rows.append(
            chunk_df
        )

        time.sleep(0.15)

    if not all_rows:
        return pd.DataFrame()

    df = pd.concat(
        all_rows,
        ignore_index=True
    )

    df = clean_dataframe(df)

    # One row per:
    # settlement period + fuel
    if all(
        column in df.columns
        for column in [
            "settlementDate",
            "settlementPeriod",
            "fuelType"
        ]
    ):

        df = (
            df.sort_values(
                [
                    "settlementDate",
                    "settlementPeriod",
                    "fuelType",
                    "publishTime"
                ]
            )
            .drop_duplicates(
                subset=[
                    "settlementDate",
                    "settlementPeriod",
                    "fuelType"
                ],
                keep="last"
            )
        )

    return (
        df.reset_index(
            drop=True
        )
    )


# ============================================================
# DOWNLOAD INDO
# ============================================================

def fetch_indo(
    start_date,
    end_date
):

    all_rows = []

    chunks = list(
        make_date_chunks(
            start_date,
            end_date,
            CHUNK_DAYS
        )
    )

    for number, (
        chunk_start,
        chunk_end
    ) in enumerate(
        chunks,
        start=1
    ):

        print(
            f"  INDO "
            f"{number}/{len(chunks)}: "
            f"{chunk_start} -> "
            f"{chunk_end}"
        )

        from_datetime = (
            f"{chunk_start}"
            f"T00:00:00Z"
        )

        # Allow publication after
        # the final settlement period.
        publication_end = (
            chunk_end
            + timedelta(days=1)
        )

        to_datetime = (
            f"{publication_end}"
            f"T01:00:00Z"
        )

        params = {
            "publishDateTimeFrom":
                from_datetime,

            "publishDateTimeTo":
                to_datetime,

            "format":
                "json"
        }

        rows = request_json(
            "/datasets/INDO",
            params
        )

        chunk_df = (
            pd.json_normalize(
                rows
            )
        )

        # Critical:
        # publication timestamps can return
        # a settlement period from the
        # previous calendar day.
        chunk_df = (
            filter_settlement_dates(
                chunk_df,
                chunk_start,
                chunk_end
            )
        )

        all_rows.append(
            chunk_df
        )

        time.sleep(0.15)

    if not all_rows:
        return pd.DataFrame()

    df = pd.concat(
        all_rows,
        ignore_index=True
    )

    df = clean_dataframe(df)

    if all(
        column in df.columns
        for column in [
            "settlementDate",
            "settlementPeriod"
        ]
    ):

        df = (
            df.sort_values(
                [
                    "settlementDate",
                    "settlementPeriod",
                    "publishTime"
                ]
            )
            .drop_duplicates(
                subset=[
                    "settlementDate",
                    "settlementPeriod"
                ],
                keep="last"
            )
        )

    return (
        df.reset_index(
            drop=True
        )
    )


# ============================================================
# VALIDATE SETTLEMENT PERIODS
# ============================================================

def settlement_period_count(df):

    if df.empty:
        return 0

    required = {
        "settlementDate",
        "settlementPeriod"
    }

    if not required.issubset(
        df.columns
    ):

        return 0

    return (
        df[
            [
                "settlementDate",
                "settlementPeriod"
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )


# ============================================================
# PRINT YEAR QA
# ============================================================

def print_year_validation(
    year,
    fuelhh,
    indo
):

    print(
        "\n"
        + "-" * 70
    )

    print(
        f"{year} DATA QUALITY CHECK"
    )

    print(
        "-" * 70
    )

    fuel_periods = (
        settlement_period_count(
            fuelhh
        )
    )

    demand_periods = (
        settlement_period_count(
            indo
        )
    )

    print(
        f"FUELHH rows: "
        f"{len(fuelhh):,}"
    )

    print(
        f"FUELHH unique "
        f"settlement periods: "
        f"{fuel_periods:,}"
    )

    print(
        f"INDO rows: "
        f"{len(indo):,}"
    )

    print(
        f"INDO unique "
        f"settlement periods: "
        f"{demand_periods:,}"
    )

    if (
        fuel_periods
        == demand_periods
    ):

        print(
            "Period coverage: MATCH"
        )

    else:

        print(
            "Period coverage: "
            "CHECK REQUIRED"
        )


# ============================================================
# CREATE WIDE GENERATION TABLE
# ============================================================

def build_generation_wide(
    fuelhh
):

    if fuelhh.empty:
        return pd.DataFrame()

    generation = (
        fuelhh.pivot_table(
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

    generation.columns.name = None

    # Research-friendly column names
    rename_map = {}

    for column in generation.columns:

        if column not in [
            "settlementDate",
            "settlementPeriod"
        ]:

            rename_map[column] = (
                f"generation_"
                f"{str(column).lower()}"
                f"_mw"
            )

    generation = (
        generation.rename(
            columns=rename_map
        )
    )

    return generation


# ============================================================
# CREATE YEARLY MASTER DATASET
# ============================================================

def build_year_dataset(
    fuelhh,
    indo
):

    generation = (
        build_generation_wide(
            fuelhh
        )
    )

    if indo.empty:
        demand = pd.DataFrame()

    else:

        demand = (
            indo[
                [
                    "settlementDate",
                    "settlementPeriod",
                    "startTime",
                    "demand"
                ]
            ]
            .copy()
            .rename(
                columns={
                    "startTime":
                        "timestamp_utc",

                    "demand":
                        "demand_mw"
                }
            )
        )

    if generation.empty:
        return demand

    if demand.empty:
        return generation

    master = pd.merge(
        demand,
        generation,
        on=[
            "settlementDate",
            "settlementPeriod"
        ],
        how="outer",
        validate="one_to_one"
    )

    master = master.sort_values(
        [
            "settlementDate",
            "settlementPeriod"
        ]
    )

    return (
        master.reset_index(
            drop=True
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "PROJECT 1 - GB HISTORICAL "
        "MARKET DATA"
    )

    print(
        "ELEXON 2022-2025"
    )

    print(
        "=" * 70
    )

    all_years = []

    for year in range(
        START_YEAR,
        END_YEAR + 1
    ):

        start_date = date(
            year,
            1,
            1
        )

        end_date = date(
            year,
            12,
            31
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"DOWNLOADING {year}"
        )

        print(
            "=" * 70
        )


        # ----------------------------------------------------
        # FUELHH
        # ----------------------------------------------------

        print(
            "\nDownloading "
            "generation by fuel..."
        )

        fuelhh = fetch_fuelhh(
            start_date,
            end_date
        )

        fuel_path = (
            RAW_DIR
            / f"fuelhh_{year}.csv"
        )

        fuelhh.to_csv(
            fuel_path,
            index=False
        )

        print(
            f"\nSaved:\n"
            f"{fuel_path}"
        )


        # ----------------------------------------------------
        # INDO
        # ----------------------------------------------------

        print(
            "\nDownloading "
            "national demand..."
        )

        indo = fetch_indo(
            start_date,
            end_date
        )

        indo_path = (
            RAW_DIR
            / f"indo_{year}.csv"
        )

        indo.to_csv(
            indo_path,
            index=False
        )

        print(
            f"\nSaved:\n"
            f"{indo_path}"
        )


        # ----------------------------------------------------
        # QA
        # ----------------------------------------------------

        print_year_validation(
            year,
            fuelhh,
            indo
        )


        # ----------------------------------------------------
        # BUILD YEAR DATASET
        # ----------------------------------------------------

        year_dataset = (
            build_year_dataset(
                fuelhh,
                indo
            )
        )

        year_dataset[
            "year"
        ] = year

        year_path = (
            PROCESSED_DIR
            / (
                f"gb_market_core_"
                f"{year}.csv"
            )
        )

        year_dataset.to_csv(
            year_path,
            index=False
        )

        print(
            f"\nProcessed "
            f"{year} dataset:"
        )

        print(
            year_dataset.shape
        )

        print(
            f"Saved:\n"
            f"{year_path}"
        )

        all_years.append(
            year_dataset
        )


    # ========================================================
    # COMBINE FOUR YEARS
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "COMBINING 2022-2025"
    )

    print(
        "=" * 70
    )

    combined = pd.concat(
        all_years,
        ignore_index=True
    )

    combined = combined.sort_values(
        [
            "settlementDate",
            "settlementPeriod"
        ]
    )

    final_path = (
        PROCESSED_DIR
        / (
            "gb_market_core_"
            "2022_2025.csv"
        )
    )

    combined.to_csv(
        final_path,
        index=False
    )

    print(
        "\nFinal dataset shape:"
    )

    print(
        combined.shape
    )

    print(
        "\nFinal columns:"
    )

    for column in combined.columns:
        print(
            f"  {column}"
        )

    print(
        "\nFinal file:"
    )

    print(
        final_path
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "ELEXON 2022-2025 "
        "DOWNLOAD COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()