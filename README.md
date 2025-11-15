# Water Quality Data Dashboard

A full-stack environmental monitoring platform for processing, analyzing, and visualizing water quality data collected by autonomous surface vehicles (ASVs) in FIU's Biscayne Bay marine robotics expeditions.

https://github.com/gregorymurad/marineRobotics


## Contributors

- [@AndrewPuig77](https://github.com/AndrewPuig77) - Andrew Puig - Collaborator
- [@devsingh1625](https://github.com/devsingh1625) — Devpreet Singh — Collaborator
- [@MCobos3](https://github.com/MCobos3) — Matt Cobos — Collaborator
- [@Sword105](https://github.com/Sword105) — Ethan Drouillard - Collaborator

---

##  Table of Contents

- [Overview](#overview)
- [Features & Dashboard](#features--dashboard)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Data Processing](#data-processing)

---

##  Overview

This project provides a comprehensive solution for environmental researchers and scientists to:
- Clean and process raw water quality sensor data
- Query data through a RESTful API with advanced filtering
- Visualize environmental trends and patterns interactively
- Detect anomalies and outliers in real-time

The system handles temperature (°C), salinity (ppt), dissolved oxygen (mg/L), pH levels, and other geolocation data collected from marine robotics expeditions in Biscayne Bay, Florida.

---

##  Features & Dashboard

###  Interactive Data Table with Filters

[Dashboard Overview]<img width="3648" height="1946" alt="Screenshot 2025-11-15 180209" src="https://github.com/user-attachments/assets/262dcc69-7a04-4a07-a7d5-8016446d6e90" />

Left Sidebar - Filter Controls
1. Date Filtering

Single Date Mode: Select a specific date to view data from that day only
Date Range Mode: Choose start and end dates to analyze trends over time

2. Temperature Range (°C)

Min Temp: Set lower temperature threshold (e.g., 26°C)
Max Temp: Set upper temperature threshold (e.g., 30°C)

3. Salinity Range (ppt - parts per thousand)

Min Salinity: Filter for low salinity zones (freshwater influence)
Max Salinity: Filter for high salinity zones (ocean water)
Use Case: Identify estuarine mixing zones or freshwater intrusion areas

4. Dissolved Oxygen - ODO Range (mg/L)

Min ODO: Set minimum oxygen threshold (e.g., 4.0 mg/L)
Max ODO: Set maximum oxygen threshold (e.g., 6.0 mg/L)

5. Pagination Controls

Limit: Records per page (100-1000)
Skip: Navigate through pages of results

The main dashboard displays water quality observations in an interactive table with:
- **Date Range Filtering**: Filter data by specific date ranges (e.g., 11/08/25 → 11/15/25)
- **Real-time Metrics**: Shows total matching records (6,550), returned records (100), and current page (1/66)
- **Pagination Controls**: Navigate through large datasets efficiently with Previous/Next buttons
- **Multi-Column Display**: View date, time, latitude, longitude, temperature, salinity, and ODO simultaneously

**Why this matters**: Environmental researchers need to quickly access specific time periods to study seasonal patterns, identify trends, or investigate particular events like algae blooms or temperature anomalies.

---

###  Summary Statistics Panel

[Summary Statistics]<img width="3222" height="953" alt="Screenshot 2025-11-15 155232" src="https://github.com/user-attachments/assets/9bf5cfd5-67f3-4143-ae96-923736331d45" />


Comprehensive statistical overview across multiple parameters:

**Temperature**
- Min: 26.60°C | Max: 32.10°C | Mean: 28.69°C
- Count: 6,550 measurements

**Salinity**
- Min: 2.63 ppt | Max: 50.12 ppt | Mean: 32.51 ppt
- Shows wide variation indicating different water zones

**Dissolved Oxygen (ODO)**
- Min: 2.42 mg/L | Max: 7.98 mg/L | Mean: 5.02 mg/L
- Critical for aquatic life assessment

**Additional Metrics**: Latitude, Longitude, pH levels with percentile distributions (P25, P50, P75)

**Why this matters**: Quick statistical summaries help researchers understand the overall data distribution, identify normal ranges, and spot potential data quality issues before deep analysis.

---

###  Visualizations

#### Temperature Over Time
Track temporal trends and seasonal patterns in water temperature.

#### Salinity Distribution

<img width="3194" height="929" alt="Screenshot 2025-11-15 155132" src="https://github.com/user-attachments/assets/6d97fc6c-bc67-4a7d-b645-24f632558223" />


This histogram shows the frequency distribution of salinity measurements:
- **Peak concentration** around 49.7 ppt (parts per thousand)
- **Normal seawater range**: Most measurements cluster between 49.2 - 49.8 ppt
- **Outliers visible** at lower ranges (49.3, 49.4, 49.5 ppt)

**Why this matters**: Salinity distribution helps identify:
- Freshwater intrusion from land runoff
- Areas with different water masses
- Mixing zones between ocean and estuary
- Potential habitat boundaries for marine species

---

#### Temperature vs Salinity Correlation

<img width="3202" height="1038" alt="Screenshot 2025-11-15 155112" src="https://github.com/user-attachments/assets/575fea35-f7f9-49f0-a57a-3b8fc040a5c9" />


This scatter plot reveals relationships between temperature and salinity, colored by dissolved oxygen (ODO) levels:
- **X-axis**: Temperature (°C) ranging from ~26.8 to 26.9
- **Y-axis**: Salinity (ppt) ranging from ~49.2 to 49.8
- **Color scale**: ODO levels from 4.0 (purple) to 5.0+ (yellow) mg/L

**Key Insights**:
- Most data points cluster tightly, indicating stable conditions
- Higher ODO (yellow points) appears at specific temperature-salinity combinations
- Vertical clustering suggests salinity varies more than temperature in this dataset

**Why this matters**: 
- Temperature-salinity relationships indicate water mass characteristics
- ODO patterns help identify oxygen-rich vs oxygen-poor zones
- Critical for understanding marine habitat suitability
- Helps predict where fish and other organisms thrive

---

#### Geographic Distribution Map

<img width="3506" height="1508" alt="Screenshot 2025-11-15 155155" src="https://github.com/user-attachments/assets/d87cbdba-b66e-4682-aa41-36f8ae9d4bfe" />


Interactive map showing the exact path of the autonomous surface vehicle during data collection:
- **Location**: Near FIU Biscayne Bay Campus
- **Path tracking**: Blue line shows ASV trajectory
- **Hover functionality**: Click any point to see temperature, salinity, ODO, and timestamp

**Why this matters**: 
- Spatial context for understanding data variations
- Identify sampling coverage gaps
- Correlate measurements with physical geography
- Plan future sampling routes

---

###  Outlier Detection

Advanced statistical outlier detection with two methods:

**Z-Score Method** (shown in screenshot):
- **Field**: Temperature selected
- **Method**: Z-score (parametric method)
- **K value**: 3.00 (threshold for standard deviations)
- **Results**: 4 outliers found
- **Detection Statistics**: Mean: 28.69, Std Dev: 1.14

**Example Outliers Detected**:
| Temperature | Latitude | Longitude | Date | Z-Score |
|-------------|----------|-----------|------|---------|
| 32.1°C | 25.881 | -80.1469 | 10/21/21 | 3.0014 |

**Why Outlier Detection is Critical**:

1. **Data Quality Assurance**
   - Identifies sensor malfunctions or calibration errors
   - Detects transmission errors in wireless data collection
   - Flags physically impossible values (e.g., negative salinity)

2. **Environmental Anomaly Detection**
   - Spots unusual events like thermal discharge
   - Identifies pollution incidents
   - Detects harmful algae bloom indicators

3. **Scientific Integrity**
   - Ensures statistical analyses aren't skewed by bad data
   - Maintains credibility of research findings
   - Supports peer-reviewed publication standards

4. **Real-World Applications**
   - Early warning system for environmental hazards
   - Validates autonomous sensor operation
   - Guides maintenance and recalibration schedules

**Two Detection Methods**:
- **Z-Score**: Best for normally distributed data, measures standard deviations from mean
- **IQR (Interquartile Range)**: More robust to non-normal distributions, uses quartile-based thresholds

**Download Functionality**: Export outliers as CSV for detailed investigation and reporting

---

##  Technology Stack

**Backend**
- **Flask**: RESTful API framework
- **MongoDB**: NoSQL database for flexible document storage
- **Pandas & NumPy**: Data processing and statistical analysis

**Frontend**
- **Streamlit**: Interactive dashboard framework
- **Plotly**: Dynamic, responsive visualizations

**Data Processing**
- **Z-score Analysis**: Statistical outlier detection
- **CSV Processing**: Automated data ingestion pipeline

---

##  Architecture

```
┌─────────────────┐
│   Raw CSV Data  │
│  (ASV Sensors)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Data Cleaning Pipeline │
│  (main.py)              │
│  - Z-score outlier      │
│    detection (k=3.0)    │
│  - CSV consolidation    │
│  - Data validation      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   MongoDB Database      │
│   (water_quality_data)  │
│   - Collection: asv_1   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│    Flask REST API       │
│    (app.py)             │
│  - /api/observations    │
│  - /api/stats           │
│  - /api/outliers        │
│  - /api/dates           │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Streamlit Dashboard    │
│  (streamlit.py)         │
│  - Interactive filters  │
│  - Plotly charts        │
│  - Real-time queries    │
└─────────────────────────┘
```

---

## Project Structure

```
.
├── api/
│   └── app.py                 # Flask REST API server
├── main/
│   └── main.py               # Data cleaning & MongoDB ingestion
├── client/
│   └── streamlit.py          # Interactive dashboard
├── data/
│   ├── source_data/          # Raw CSV files from ASV
│   └── cleaned.csv           # Processed dataset
├── requirements.txt          # Python dependencies
├── .env                      # MongoDB credentials (not in repo)
└── README.md                 # This file
```

---

##  Quick Start (Windows, PowerShell)

### 1. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the repository root:

```env
MONGODB_URI=cluster0.xxxxx.mongodb.net
MONGO_USER=your_mongo_user
MONGO_PASS=your_mongo_password
```

**Note**: `MONGODB_URI` should be the host portion only (without `mongodb+srv://`)

### 4. Process and Clean Data

```powershell
python main/main.py
```

This will:
- Load CSV files from `data/source_data/`
- Apply Z-score outlier detection (k=3.0)
- Export cleaned data to `data/cleaned.csv`
- Insert records into MongoDB

### 5. Start Flask API Server

```powershell
python api/app.py
```

API runs on `http://127.0.0.1:5000`

### 6. Launch Streamlit Dashboard

Open a **new terminal**, activate the virtual environment, then run:

```powershell
streamlit run client/streamlit.py
```

Dashboard opens at `http://localhost:8501`

---

##  API Documentation

### Base URL
```
http://127.0.0.1:5000/api
```

All responses are JSON format.

---

### GET `/api/health`

Health check endpoint for monitoring.

**Response**:
```json
{ "status": "ok" }
```

---

### GET `/api/dates`

Returns distinct date values from the database.

**Response**:
```json
{
  "dates": ["12/16/21", "10/21/21", "11/08/25", ...]
}
```

**Use Case**: Populate date picker dropdowns in UI

---

### GET `/api/observations`

Query water quality observations with filtering and pagination.

**Query Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `limit` | int | Records per page (max: 1000) | `100` |
| `skip` | int | Pagination offset | `0` |
| `date` | string | Exact date match (MM/DD/YY) | `12/16/21` |
| `date_start` | string | Range start date | `11/08/25` |
| `date_end` | string | Range end date | `11/15/25` |
| `min_temp` | float | Minimum temperature (°C) | `26.0` |
| `max_temp` | float | Maximum temperature (°C) | `30.0` |
| `min_sal` | float | Minimum salinity (ppt) | `30.0` |
| `max_sal` | float | Maximum salinity (ppt) | `35.0` |
| `min_odo` | float | Minimum dissolved oxygen (mg/L) | `4.0` |
| `max_odo` | float | Maximum dissolved oxygen (mg/L) | `6.0` |

**Example Request**:
```
GET /api/observations?limit=100&skip=0&date_start=11/08/25&date_end=11/15/25&min_temp=26.0&max_temp=30.0
```

**Response**:
```json
{
  "count": 6550,
  "returned": 100,
  "items": [
    {
      "date": "12/16/21",
      "Time": "44:20.0",
      "latitude": 25.9121,
      "longitude": -80.1374,
      "temperature": 26.8,
      "salinity": 49.73,
      "odo": 4.02,
      "pH": 8.15
    },
    ...
  ]
}
```

**Date Range Note**: The API converts MM/DD/YY strings to YYYY-MM-DD internally for proper chronological sorting using MongoDB aggregation.

---

### GET `/api/stats`

Calculate summary statistics for numeric fields.

**Query Parameters**:
- `fields` (comma-separated) - Which fields to analyze (default: `temperature,salinity,odo`)

**Example Request**:
```
GET /api/stats?fields=temperature,salinity,odo
```

**Response**:
```json
{
  "temperature": {
    "min": 26.60,
    "max": 32.10,
    "avg": 28.69,
    "stddev": 1.14
  },
  "salinity": {
    "min": 2.63,
    "max": 50.12,
    "avg": 32.51,
    "stddev": 8.42
  },
  "odo": {
    "min": 2.42,
    "max": 7.98,
    "avg": 5.02,
    "stddev": 0.95
  }
}
```

---

### GET `/api/outliers`

Detect statistical outliers using Z-score or IQR methods.

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `field` | string | Yes | Field to analyze (`temperature`, `salinity`, `odo`) |
| `method` | string | No | Detection method: `zscore` or `iqr` (default: `zscore`) |
| `k` | float | No | Threshold value (default: 3.0 for zscore, 1.5 for iqr) |

**Example Request (Z-Score)**:
```
GET /api/outliers?field=temperature&method=zscore&k=3.0
```

**Response**:
```json
{
  "count": 4,
  "outliers": [
    {
      "temperature": 32.1,
      "latitude": 25.881,
      "longitude": -80.1469,
      "date": "10/21/21",
      "z_score": 3.0014
    },
    ...
  ],
  "method": "zscore",
  "field": "temperature",
  "k": 3.0,
  "statistics": {
    "mean": 28.69,
    "stddev": 1.14
  }
}
```

**Example Request (IQR)**:
```
GET /api/outliers?field=salinity&method=iqr&k=1.5
```

**Response**:
```json
{
  "count": 12,
  "outliers": [...],
  "method": "iqr",
  "field": "salinity",
  "k": 1.5,
  "statistics": {
    "q1": 18.97,
    "q3": 46.35,
    "iqr": 27.38,
    "lower_bound": -22.10,
    "upper_bound": 87.42
  }
}
```

---



##  Dataset Information

**Source**: FIU Marine Robotics - Biscayne Bay Expeditions  
**Collection Method**: Autonomous Surface Vehicle (ASV) sensors  
**Paramaters measured include**:
- Temperature (°C)
- Salinity (ppt - parts per thousand)
- Dissolved Oxygen (mg/L)
- pH levels
- GPS coordinates (latitude/longitude)
- Timestamp
- and more




