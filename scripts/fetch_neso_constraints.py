from pathlib import Path
import re
import time

import pandas as pd
import requests


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
    / "neso"
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
# NESO CKAN API
# ============================================================

BASE_URL = (
    "https://api.neso.energy/"
    "api/3/action/datastore_search"
)


# ============================================================
# RESOURCE IDS
#
# Constraint Breakdown Costs and Volume
#
# We use five financial years so that calendar
# years 2022-2025 are completely covered.
# ============================================================

RESOURCES = {

    "2021-2022":
        "419337fb-f609-45e3-9097-798a41b4b3de",

    "2022-2023":
        "efb633ae-f6d7-444b-8759-449ac0539dd0",

    "2023-2024":
        "24d067d8-1328-452a-9720-21cb691e491e",

    "2024-2025":
        "748557ef-2bb3-41c0-8181-5f1a148c1ff4",

    "2025-2026":
        "6afe1c2b-6d70-4e76-8e74-0952b0a2beab",
}


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent":
        "PyPSA-GB Research Project / "
        "GB Constraint Analysis"
    }
)


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean_column_name(name):

    name = str(name).strip()

    name = name.lower()

    name = name.replace(
        "£",
        "gbp"
    )

    name = name.replace(
        "/",
        "_"
    )

    name = re.sub(
        r"[^a-z0-9]+",
        "_",
        name
    )

    name = name.strip("_")

    return name


# ============================================================
# DOWNLOAD COMPLETE CKAN RESOURCE
# ============================================================

def fetch_resource(
    resource_id,
    page_size=5000
):

    all_records = []

    offset = 0

    while True:

        params = {
            "resource_id":
                resource_id,

            "limit":
                page_size,

            "offset":
                offset
        }

        print(
            f"    Request offset "
            f"{offset:,}"
        )

        response = SESSION.get(
            BASE_URL,
            params=params,
            timeout=90
        )

        response.raise_for_status()

        payload = response.json()

        if not payload.get(
            "success",
            False
        ):

            raise RuntimeError(
                "NESO API returned "
                "success=False"
            )

        result = payload[
            "result"
        ]

        records = result.get(
            "records",
            []
        )

        total = int(
            result.get(
                "total",
                0
            )
        )

        all_records.extend(
            records
        )

        print(
            f"    Received "
            f"{len(records):,} records "
            f"(total resource: "
            f"{total:,})"
        )

        offset += len(
            records
        )

        if (
            len(records) == 0
            or offset >= total
        ):

            break

        # NESO recommends keeping CKAN
        # requests to roughly one per second.
        time.sleep(1.1)

    return pd.json_normalize(
        all_records
    )


# ============================================================
# IDENTIFY DATE COLUMN
# ============================================================

def find_date_column(df):

    candidates = [
        column
        for column in df.columns
        if clean_column_name(
            column
        ) == "date"
    ]

    if candidates:

        return candidates[0]

    # Fallback if naming changes slightly
    candidates = [
        column
        for column in df.columns
        if "date" in
        clean_column_name(
            column
        )
    ]

    if candidates:

        return candidates[0]

    raise ValueError(
        "Could not identify a date "
        "column in NESO dataset."
    )


# ============================================================
# PREPARE RESOURCE
# ============================================================

def prepare_resource(
    df,
    financial_year
):

    if df.empty:

        return df

    print(
        "\n    Original columns:"
    )

    for column in df.columns:

        print(
            f"      {column}"
        )


    # ----------------------------------------
    # Identify date before renaming
    # ----------------------------------------

    raw_date_column = (
        find_date_column(
            df
        )
    )


    # ----------------------------------------
    # Standardise column names
    # ----------------------------------------

    rename_map = {
        column:
            clean_column_name(
                column
            )
        for column in df.columns
    }

    df = df.rename(
        columns=rename_map
    )


    date_column = (
        clean_column_name(
            raw_date_column
        )
    )


    # ----------------------------------------
    # Parse date
    # ----------------------------------------

    df[
        date_column
    ] = pd.to_datetime(
        df[
            date_column
        ],
        errors="coerce"
    )


    df = df.rename(
        columns={
            date_column:
                "date"
        }
    )


    # ----------------------------------------
    # Add provenance
    # ----------------------------------------

    df[
        "financial_year"
    ] = financial_year


    # ----------------------------------------
    # Remove CKAN internal row id
    # ----------------------------------------

    if "_id" in df.columns:

        df = df.drop(
            columns=[
                "_id"
            ]
        )


    # ----------------------------------------
    # Convert likely numeric fields
    # ----------------------------------------

    for column in df.columns:

        if column in [
            "date",
            "financial_year"
        ]:

            continue

        df[column] = (
            df[column]
            .astype(str)
            .str.replace(
                ",",
                "",
                regex=False
            )
            .str.replace(
                "£",
                "",
                regex=False
            )
        )

        numeric = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        # Only replace with numeric version
        # when meaningful numbers exist.
        if numeric.notna().sum() > 0:

            df[
                column
            ] = numeric


    return df


# ============================================================
# BASIC QUALITY CHECK
# ============================================================

def print_resource_summary(
    name,
    df
):

    print(
        "\n"
        + "-" * 70
    )

    print(
        f"{name} QA"
    )

    print(
        "-" * 70
    )

    print(
        f"Rows: "
        f"{len(df):,}"
    )

    if (
        not df.empty
        and "date"
        in df.columns
    ):

        print(
            "Date range:",
            df["date"].min(),
            "->",
            df["date"].max()
        )

        print(
            "Unique dates:",
            df[
                "date"
            ].nunique()
        )

        duplicates = (
            df[
                "date"
            ]
            .duplicated()
            .sum()
        )

        print(
            "Duplicate dates:",
            duplicates
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "PROJECT 1 - NESO "
        "CONSTRAINT DATA PIPELINE"
    )

    print(
        "=" * 70
    )

    all_resources = []


    # ========================================================
    # DOWNLOAD EACH FINANCIAL YEAR
    # ========================================================

    for financial_year, (
        resource_id
    ) in RESOURCES.items():

        print(
            "\n"
            + "=" * 70
        )

        print(
            f"DOWNLOADING "
            f"{financial_year}"
        )

        print(
            "=" * 70
        )


        raw = fetch_resource(
            resource_id
        )


        # ----------------------------------------------------
        # Save untouched API response
        # ----------------------------------------------------

        raw_path = (
            RAW_DIR
            / (
                "constraint_breakdown_"
                f"{financial_year}.csv"
            )
        )

        raw.to_csv(
            raw_path,
            index=False
        )

        print(
            f"\nRaw saved:"
            f"\n{raw_path}"
        )


        # ----------------------------------------------------
        # Standardise
        # ----------------------------------------------------

        clean = prepare_resource(
            raw,
            financial_year
        )


        print_resource_summary(
            financial_year,
            clean
        )


        all_resources.append(
            clean
        )


        # One-second API spacing
        time.sleep(1.1)


    # ========================================================
    # COMBINE
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "COMBINING NESO DATA"
    )

    print(
        "=" * 70
    )


    combined = pd.concat(
        all_resources,
        ignore_index=True,
        sort=False
    )


    # ========================================================
    # FILTER EXACT RESEARCH WINDOW
    # ========================================================

    research_start = (
        pd.Timestamp(
            "2022-01-01"
        )
    )

    research_end = (
        pd.Timestamp(
            "2025-12-31"
        )
    )


    combined = combined[
        (
            combined[
                "date"
            ]
            >= research_start
        )
        &
        (
            combined[
                "date"
            ]
            <= research_end
        )
    ].copy()


    # ========================================================
    # SORT
    # ========================================================

    combined = (
        combined
        .sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )


    # ========================================================
    # SAVE
    # ========================================================

    output_path = (
        PROCESSED_DIR
        / (
            "neso_constraint_breakdown_"
            "2022_2025.csv"
        )
    )

    combined.to_csv(
        output_path,
        index=False
    )


    # ========================================================
    # FINAL QA
    # ========================================================

    print(
        "\nFinal dataset shape:"
    )

    print(
        combined.shape
    )


    print(
        "\nDate range:"
    )

    print(
        combined[
            "date"
        ].min(),
        "->",
        combined[
            "date"
        ].max()
    )


    print(
        "\nFinal columns:"
    )

    for column in (
        combined.columns
    ):

        print(
            f"  {column}"
        )


    print(
        "\nMissing values "
        "per column:"
    )

    print(
        combined
        .isna()
        .sum()
    )


    print(
        "\nFinal file:"
    )

    print(
        output_path
    )


    print(
        "\n"
        + "=" * 70
    )

    print(
        "NESO CONSTRAINT "
        "DOWNLOAD COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()