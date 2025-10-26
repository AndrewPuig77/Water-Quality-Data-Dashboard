import pandas as pd
import numpy as np
import pymongo
from dotenv import load_dotenv
import os
import glob
import os
from pymongo.errors import BulkWriteError


# -------- Load and Combine CSV Files --------
# Look for source CSVs in several possible locations. Some copies of the
# project put source CSVs in `source_data/`, others under `data/source_data/`.
candidates = [
    os.path.join("data", "source_data", "*.csv"),
    os.path.join("source_data", "*.csv"),
    os.path.join("data", "*.csv"),
]

csv_files = []
for pattern in candidates:
    found = glob.glob(pattern)
    if found:
        csv_files.extend(found)

# Deduplicate and normalize
csv_files = sorted(list(dict.fromkeys(csv_files)))

if not csv_files:
    print("No source CSV files found. Looked in:")
    for p in candidates:
        print(f"  - {p}")
    print("Place your input CSV files in one of the above locations (for example: data/source_data/) and re-run the script.")
    raise SystemExit(1)

df_list = [pd.read_csv(f) for f in csv_files]
df = pd.concat(df_list, ignore_index=True)


# print("Columns in dataset:")
# print(df.columns.tolist())

print("Loaded files:", [os.path.basename(f) for f in csv_files])
print("Total rows:", len(df))
print(df.head())


# columns to z-score
NUMERIC_COLS = ["Temperature (c)", "Salinity (ppt)", "ODO mg/L"]

# ensure numeric (non-numeric -> NaN)
df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric, errors="coerce")

# compute z-scores across the whole combined dataset
means = df[NUMERIC_COLS].mean()
stds = df[NUMERIC_COLS].std(ddof=0) 
stds = stds.replace(0, np.nan) # avoid divide-by-zero
z = (df[NUMERIC_COLS] - means) / stds

THRESH = 3.0
is_outlier = (z.abs() > THRESH).any(axis=1)

# report
total_rows = len(df)
removed_rows = int(is_outlier.sum())
remaining_rows = total_rows - removed_rows

print("=== Cleaning Report ===")
print(f"Total rows originally:          {total_rows}")
print(f"Rows removed as outliers:       {removed_rows}")
print(f"Rows remaining after cleaning:  {remaining_rows}")

# drop outliers
df_clean = df.loc[~is_outlier].copy()
df_clean = df_clean.dropna(subset=NUMERIC_COLS)

output_dir = "data"
os.makedirs(output_dir, exist_ok=True)  # create folder if it doesn't exist

output_path = os.path.join(output_dir, "cleaned.csv")
df_clean.to_csv(output_path, index=False)
print(f"Cleaned data saved to {output_path}")


# -------- Save to MongoDB --------
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")

print("MONGO_URI:", MONGO_URI)
print("MONGO_USER:", MONGO_USER)
# Do not print MONGO_PASS in production logs; this is helpful for local debugging only

# Attempt to connect to a real MongoDB instance first. If credentials are missing
# or the connection fails, fall back to an in-memory mongomock instance so the
# script can run without a running MongoDB server (useful for development/tests).
if not all([MONGO_URI, MONGO_USER, MONGO_PASS]):
    print("MongoDB credentials are missing. Please set MONGODB_URI, MONGO_USER, and MONGO_PASS in your .env file.")
    raise SystemExit(1)

url = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_URI}/?retryWrites=true&w=majority"
print("Attempting MongoDB connection to:", url)
try:
    client = pymongo.MongoClient(url, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("MongoDB client created")
except Exception as e:
    print("MongoDB connection error:", e)
    print("Ensure MongoDB is accessible and your credentials are correct.")
    raise SystemExit(1)

# Select database and collection
db = client["water_quality_data"]
collection = db["asv_1"]

# Clear the collection before inserting cleaned records (intentional behavior)
collection.delete_many({})

df_clean = df_clean.rename(columns={
    "Temperature (c)": "temperature",
    "Salinity (ppt)": "salinity",
    "ODO mg/L": "odo",
    "Date": "date",
    "Latitude": "latitude",
    "Longitude": "longitude"
})

df_clean = df_clean.replace({np.nan: None})

records = df_clean.to_dict("records")
if records:  
    collection.insert_many(records)


print("Total documents in collection:", collection.count_documents({}))
print("First document:")
print(collection.find_one())