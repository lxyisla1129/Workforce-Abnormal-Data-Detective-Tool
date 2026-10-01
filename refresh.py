from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from Scraping import get_attendance_data

import time
import requests

MAX_ATTEMPTS = 3
RETRY_WAIT = 30 * 60  # 30 minutes

# =========================================================
# FILE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data"
DATA_FOLDER.mkdir(exist_ok=True)

DATA_FILE = DATA_FOLDER / "AMS_Attendance_Data.xlsx"
TEMP_FILE = DATA_FOLDER / "AMS_Attendance_Data_temp.xlsx"


# =========================================================
# PAST 7 COMPLETED DAYS
# =========================================================

today = datetime.now().date()
end_date = today - timedelta(days=1)       # yesterday
start_date = end_date - timedelta(days=6)  # 7 days total

print(f"Refreshing: {start_date} → {end_date}")


# =========================================================
# GET FRESH 7-DAY DATA
# =========================================================

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        print(f"Scraping attempt {attempt}/{MAX_ATTEMPTS}...")

        new_df = get_attendance_data(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )

        # Success → stop retrying
        break

    except requests.exceptions.ConnectionError as e:
        print(f"Connection failed on attempt {attempt}: {e}")

        if attempt < MAX_ATTEMPTS:
            print("Will retry in 30 minutes...")
            time.sleep(RETRY_WAIT)
        else:
            print("Failed after 3 attempts.")
            raise

if new_df.empty:
    raise RuntimeError(
        "API returned 0 rows. Existing Excel was NOT changed."
    )

if "eday" not in new_df.columns:
    raise RuntimeError(
        "API result does not contain eday."
    )

new_df["eday"] = pd.to_datetime(
    new_df["eday"],
    errors="coerce"
)

print("New rows:", len(new_df))
print("New data range:", new_df["eday"].min(), "→", new_df["eday"].max())


# =========================================================
# LOAD OLD DATA
# =========================================================

if DATA_FILE.exists():

    old_df = pd.read_excel(
        DATA_FILE,
        engine="openpyxl"
    )

    old_df["eday"] = pd.to_datetime(
        old_df["eday"],
        errors="coerce"
    )

    print("Existing rows:", len(old_df))

    # Remove the past 7 days from old data
    # because we're replacing them with fresh API data

    old_df = old_df[
        ~old_df["eday"].dt.date.between(
            start_date,
            end_date
        )
    ]

    # Old history + refreshed 7 days
    final_df = pd.concat(
        [old_df, new_df],
        ignore_index=True
    )

else:

    # No Excel = just create one using the fresh 7 days
    print("No existing Excel. Creating a new one.")
    final_df = new_df.copy()


# =========================================================
# REMOVE DUPLICATES
# =========================================================

if "id" in final_df.columns:

    final_df = final_df.drop_duplicates(
        subset=["id"],
        keep="last"
    )

else:

    final_df = final_df.drop_duplicates(
        subset=["userCode", "eday"],
        keep="last"
    )


# =========================================================
# SORT
# =========================================================

sort_cols = [
    col for col in [
        "eday",
        "scheduleDeptName",
        "userName"
    ]
    if col in final_df.columns
]

if sort_cols:

    final_df = final_df.sort_values(
        sort_cols,
        ascending=[
            False if col == "eday" else True
            for col in sort_cols
        ]
    )


# =========================================================
# SAFE SAVE
# =========================================================

# Write to temp first
final_df.to_excel(
    TEMP_FILE,
    index=False,
    engine="openpyxl"
)

# Make sure temp file can actually be opened
test_df = pd.read_excel(
    TEMP_FILE,
    engine="openpyxl"
)

print("Verified temp rows:", len(test_df))

# Only after successful verification replace production file
TEMP_FILE.replace(DATA_FILE)


# =========================================================
# DONE
# =========================================================

print("\nREFRESH COMPLETE")
print("Refreshed:", start_date, "→", end_date)
print("Fresh rows:", len(new_df))
print("Total rows:", len(final_df))
print("Saved to:", DATA_FILE)