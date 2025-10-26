from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import numpy as np

app = Flask(__name__)

# Connect to Mongo
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_USER = os.getenv("MONGO_USER")

if not all([MONGO_URI, MONGO_USER, MONGO_PASS]):
    print("ERROR: Missing MongoDB credentials!")
    exit(1)

url= f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_URI}/?retryWrites=true&w=majority"

client = MongoClient(url)
try:
    # The ismaster command is cheap and does not require auth
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed:", e)
    

db = client["water_quality_data"]
collection = db["asv_1"]


def _parse_iso_timestamp(ts_str):
    if ts_str is None:
        return None, None
    # Support trailing Z
    s = ts_str
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    parsed = datetime.fromisoformat(s)
    return ts_str, parsed

# In Flask app.py
def clean_nan(obj):
    """Replace NaN with None for JSON serialization"""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(item) for item in obj]
    return obj

# Use it before returning
# items = clean_nan(items)
# return jsonify({"count": total, "items": items})

#----- Health Check -----
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


#----- Get Available Dates -----
@app.route("/api/dates", methods=["GET"])
def get_dates():
    try:
        dates = collection.distinct("Date")
        dates = sorted([d for d in dates if d])
        return jsonify({"dates": dates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#----- Get Observations -----
@app.route("/api/observations", methods=["GET"])
def get_observations():
    # Build MongoDB query
    q = {}

    # Date filtering (using your actual field name)
    date = request.args.get("date")
    if date:
        q["Date"] = date

    # Numeric ranges
    def _add_range(field_name, min_arg, max_arg):
        min_v = request.args.get(min_arg)
        max_v = request.args.get(max_arg)
        if min_v is None and max_v is None:
            return
        try:
            if min_v is not None:
                min_f = float(min_v)
                q.setdefault(field_name, {})["$gte"] = min_f
            if max_v is not None:
                max_f = float(max_v)
                q.setdefault(field_name, {})["$lte"] = max_f
        except ValueError:
            raise

    try:
        _add_range("temperature", "min_temp", "max_temp")
        _add_range("salinity", "min_sal", "max_sal")
        _add_range("odo", "min_odo", "max_odo")
    except ValueError:
        return jsonify({"error": "min/max numeric parameters must be valid numbers"}), 400

    # Pagination
    try:
        limit = int(request.args.get("limit", 100))
        skip = int(request.args.get("skip", 0))
    except ValueError:
        return jsonify({"error": "limit and skip must be integers"}), 400

    if limit <= 0:
        return jsonify({"error": "limit must be > 0"}), 400
    if skip < 0:
        return jsonify({"error": "skip must be >= 0"}), 400
    
    limit = min(limit, 1000)

    # Query database
    try:
        total = collection.count_documents(q)
    except Exception:
        # In case of a query type mismatch in DB, return 400
        return jsonify({"error": "Invalid query parameters for stored document types"}), 400

    cursor = collection.find(q, {"_id": 0}).skip(skip).limit(limit)
    items = list(cursor)

    return jsonify({"count": total, "items": items})



#----- Get Stats -----
@app.route("/api/stats", methods=["GET"])
def get_stats():
    numeric_fields = ["temperature", "salinity", "odo"]
    stats = {}
    
    for field in numeric_fields:
        # Get all values for this field (excluding None/null)
        cursor = collection.find({field: {"$ne": None}}, {"_id": 0, field: 1})
        values = [doc[field] for doc in cursor if field in doc and doc[field] is not None]
        
        if len(values) == 0:
            stats[field] = {
                "count": 0,
                "mean": None,
                "min": None,
                "max": None,
                "percentiles": {
                    "25": None,
                    "50": None,
                    "75": None
                }
            }
        else:
            values_array = np.array(values)
            stats[field] = {
                "count": len(values),
                "mean": float(np.mean(values_array)),
                "min": float(np.min(values_array)),
                "max": float(np.max(values_array)),
                "percentiles": {
                    "25": float(np.percentile(values_array, 25)),
                    "50": float(np.percentile(values_array, 50)),
                    "75": float(np.percentile(values_array, 75))
                }
            }
    
    return jsonify(stats)

# ---- Get Outliers ----
app.route("/api/outliers", methods=["GET"])
def get_outliers():
    """
    Detect outliers using either Z-score or IQR method.
    
    Query parameters:
    - field: temperature, salinity, or odo (required)
    - method: zscore or iqr (default: zscore)
    - k: threshold value (default: 3.0 for zscore, 1.5 for iqr)
    """
    # Get parameters
    field = request.args.get("field")
    method = request.args.get("method", "zscore").lower()
    
    # Validate field
    valid_fields = ["temperature", "salinity", "odo"]
    if field not in valid_fields:
        return jsonify({"error": f"field must be one of {valid_fields}"}), 400
    
    # Validate method
    if method not in ["zscore", "iqr"]:
        return jsonify({"error": "method must be 'zscore' or 'iqr'"}), 400
    
    # Get k value with appropriate default
    try:
        k = float(request.args.get("k", 3.0 if method == "zscore" else 1.5))
    except ValueError:
        return jsonify({"error": "k must be a valid number"}), 400
    
    try:
        # Calculate statistics for the field
        pipeline = [
            {"$match": {field: {"$ne": None, "$exists": True}}},
            {
                "$group": {
                    "_id": None,
                    "avg": {"$avg": f"${field}"},
                    "stddev": {"$stdDevPop": f"${field}"}
                }
            }
        ]
        stats_result = list(collection.aggregate(pipeline))
        
        if not stats_result:
            return jsonify({
                "count": 0,
                "outliers": [],
                "method": method,
                "field": field,
                "k": k
            })
        
        avg = stats_result[0]["avg"]
        stddev = stats_result[0]["stddev"]
        
        if method == "zscore":
            # Z-score method
            if stddev == 0 or stddev is None:
                return jsonify({
                    "count": 0,
                    "outliers": [],
                    "method": method,
                    "field": field,
                    "k": k,
                    "message": "Standard deviation is zero, no outliers detected"
                })
            
            # Find outliers using aggregation pipeline
            outlier_pipeline = [
                {"$match": {field: {"$ne": None, "$exists": True}}},
                {
                    "$addFields": {
                        "z_score": {
                            "$divide": [
                                {"$subtract": [f"${field}", avg]},
                                stddev
                            ]
                        }
                    }
                },
                {
                    "$match": {
                        "$expr": {
                            "$gt": [
                                {"$abs": "$z_score"},
                                k
                            ]
                        }
                    }
                },
                {"$project": {"_id": 0}}
            ]
            
        else:  # IQR method
            # Calculate Q1, Q3 for IQR
            all_values = list(collection.find(
                {field: {"$ne": None, "$exists": True}},
                {field: 1, "_id": 0}
            ))
            
            if not all_values:
                return jsonify({
                    "count": 0,
                    "outliers": [],
                    "method": method,
                    "field": field,
                    "k": k
                })
            
            values = sorted([doc[field] for doc in all_values if doc.get(field) is not None])
            n = len(values)
            
            q1_idx = n // 4
            q3_idx = (3 * n) // 4
            
            q1 = values[q1_idx]
            q3 = values[q3_idx]
            iqr = q3 - q1
            
            lower_bound = q1 - k * iqr
            upper_bound = q3 + k * iqr
            
            # Find outliers
            outlier_pipeline = [
                {
                    "$match": {
                        field: {"$ne": None, "$exists": True},
                        "$or": [
                            {field: {"$lt": lower_bound}},
                            {field: {"$gt": upper_bound}}
                        ]
                    }
                },
                {"$project": {"_id": 0}}
            ]
        
        # Execute the pipeline
        outliers = list(collection.aggregate(outlier_pipeline))
        outliers = clean_nan(outliers)
        
        return jsonify({
            "count": len(outliers),
            "outliers": outliers,
            "method": method,
            "field": field,
            "k": k,
            "statistics": {
                "mean": avg,
                "stddev": stddev
            } if method == "zscore" else {
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    if not field:
        return jsonify({"error": "field parameter is required"}), 400
    
    if field not in ["temperature", "salinity", "odo"]:
        return jsonify({"error": "field must be one of: temperature, salinity, odo"}), 400
    
    if method not in ["iqr", "z-score"]:
        return jsonify({"error": "method must be 'iqr' or 'z-score'"}), 400
    
    # Get k parameter (threshold multiplier)
    k_param = request.args.get("k", "1.5")
    try:
        k = float(k_param)
    except ValueError:
        return jsonify({"error": "k must be a valid number"}), 400
    
    # Fetch all documents with the field
    cursor = collection.find({field: {"$ne": None}}, {"_id": 0})
    docs = list(cursor)
    
    if len(docs) == 0:
        return jsonify({"count": 0, "outliers": []})
    
    # Extract values
    values = np.array([doc[field] for doc in docs if field in doc and doc[field] is not None])
    
    if len(values) == 0:
        return jsonify({"count": 0, "outliers": []})
    
    # Detect outliers based on method
    outlier_indices = []
    
    if method == "iqr":
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        
        for i, val in enumerate(values):
            if val < lower_bound or val > upper_bound:
                outlier_indices.append(i)
    
    elif method == "z-score":
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            # No outliers if no variation
            return jsonify({"count": 0, "outliers": []})
        
        for i, val in enumerate(values):
            z_score = abs((val - mean) / std)
            if z_score > k:
                outlier_indices.append(i)
    
    # Get the outlier documents
    outliers = [docs[i] for i in outlier_indices]
    
    return jsonify({"count": len(outliers), "outliers": outliers})


if __name__ == "__main__":
    app.run(debug=True)