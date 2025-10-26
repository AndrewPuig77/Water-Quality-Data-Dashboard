

This repository contains a Flask API and a Streamlit client for exploring water quality observations (temperature, salinity, ODO, and geolocation data). The project demonstrates data cleaning, server-side aggregation, pagination, summary statistics, and outlier detection.

##Contributors
- [@AndrewPuig77](https://github.com/AndrewPuig77)- Andrew Puig - Collaborator
- [@devsingh1625](https://github.com/devsingh1625) — Devpreet Singh — Collaborator
- [@MCobos3](https://github.com/MCobos3) — Matt Cobos — Collaborator
- [@Sword105](https://github.com/Sword105) — Ethan Drouillard - Collaborator



## Contents

- `api/` - Flask API server
	- `app.py` - REST API for observations, stats, outliers, and health checks
- `main/` folder for main python file
    - `main.py` - CSV ingestion and cleaning (z-score based outlier removal) that produces `data/cleaned.csv` and inserts cleaned records into MongoDB
- `client/` - Streamlit dashboard
	- `streamlit.py` - Interactive dashboard to query the API and render visualizations
- `data/` - Source CSV files used for ingestion
- `data/cleaned.csv` - Cleaned dataset produced by `api/main.py`
- `requirements.txt` - Python dependencies
- `README.md` - (this file)


## Quick Start (Windows, PowerShell)

1. Create a Python virtual environment and activate it

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Configure environment variables

Create a `.env` file in the repository root with the following values (use your MongoDB Atlas or local MongoDB credentials):

```
MONGODB_URI=cluster0.xxxxx.mongodb.net
MONGO_USER=your_mongo_user
MONGO_PASS=your_mongo_password
# Optional: provide a standard connection string if SRV fails
# MONGODB_STANDARD_URI=mongodb://host1:27017,host2:27017/<dbname>
```

- Notes:
- `MONGODB_URI` should be the host portion (without `mongodb+srv://`) when using the SRV connection method constructed inside `api/app.py`.
- If you prefer a single connection string, set `MONGODB_STANDARD_URI` to a full MongoDB URI and the server will attempt that as a fallback.

4. Start the Flask API server

```powershell
python api/app.py
```

By default the API runs on `http://127.0.0.1:5000`.

5. Run csv file cleaner
```powershell
python api/main.py
```

6. Start the Streamlit client (in a separate terminal)

```powershell
streamlit run client/streamlit.py
```

Open the address printed by Streamlit (typically `http://localhost:8501`) in your browser.


## API Documentation

Base URL: `http://127.0.0.1:5000/api`

All responses are JSON. The API expects cleaned data inserted by `api/main.py` or your own dataset inserted into the `water_quality_data.asv_1` collection in MongoDB.

### GET /api/health

Returns a basic health check

Response:
```
{ "status": "ok" }
```


### GET /api/dates

Returns a list of distinct `date` string values from the database. Useful for populating date pickers.

Response:
```
{ "dates": ["12/16/21", "10/21/21", ...] }
```


### GET /api/observations

Query observations with optional filters and pagination.

Query parameters:
- `limit` (int) - number of records to return (default: 100, max: 1000)
- `skip` (int) - offset for pagination (default: 0)
- `date` (string) - exact match on stored date strings (expected format in this codebase: `MM/DD/YY`)
- `date_start` / `date_end` (string) - inclusive date range. These are parsed and compared by converting DB date strings to `YYYY-MM-DD` internally.
- `min_temp`, `max_temp` - numeric filters for `temperature`
- `min_sal`, `max_sal` - numeric filters for `salinity`
- `min_odo`, `max_odo` - numeric filters for `odo`

Example:
```
GET /api/observations?limit=100&skip=0&date=12/16/21
```

Response:
```
{
	"count": 1234,            // total matching records
	"returned": 100,         // number returned in this page
	"items": [ ... ]         // array of observation objects
}
```

Notes:
- Date range filtering uses aggregation to convert the stored `MM/DD/YY` strings to sortable `YYYY-MM-DD` strings. The API accepts 2-digit or 4-digit years but stores/compares using a normalized format internally for the range match.


### GET /api/stats

Return summary statistics for numeric fields.

Query parameters:
- `fields` (comma-separated strings) - which fields to compute stats for (defaults to `temperature,salinity,odo`)

Response:
```
{
	"temperature": { "min": 10.0, "max": 25.0, "avg": 17.5, "stddev": 2.3 },
	"salinity": { ... },
	"odo": { ... }
}
```

Currently returned stats: min, max, avg, stddev. Percentiles/count will be added in a future update.


### GET /api/outliers

Detect outliers using either the Z-score or IQR method.

Query parameters:
- `field` (string) - field name to analyze (required)
- `method` (string) - `zscore` (default) or `iqr`
- `k` (float) - threshold value (default: `3.0` for zscore, `1.5` for iqr)

Response (zscore example):
```
{
	"count": 3,
	"outliers": [ { ... }, { ... } ],
	"method": "zscore",
	"field": "temperature",
	"k": 3.0,
	"statistics": { "mean": 17.5, "stddev": 2.3 }
}
```

Response (iqr example includes IQR stats and bounds):
```
{
	"statistics": { "q1": 12.5, "q3": 19.5, "iqr": 7.0, "lower_bound": ..., "upper_bound": ... }
}
```


## Data Ingestion and Cleaning

`api/main.py` reads CSV files from `data/source_data/`, computes z-scores to identify and remove extreme outliers, and writes cleaned rows to `data/cleaned.csv`. It also inserts cleaned records into the MongoDB collection `water_quality_data.asv_1`.

If you want to re-run ingestion:

```powershell
python api/main.py
```

This script will print counts of total, removed and inserted records.

