
A short essay on the work completed for this project

Working with environmental sensor data exposes two realities quickly: the data is messy and the choices you make to clean it shape every downstream analysis. For this project I followed a pragmatic path — ingest raw CSVs, apply a conservative cleaning step based on z‑scores, store the cleaned records in MongoDB, and expose a small set of REST endpoints to support exploration via a Streamlit dashboard. Below I explain the cleaning approach, why the endpoints are designed the way they are, and a few lessons learned along the way.

Cleaning the data: why z‑score and how it was applied

Sensor datasets often contain clear errors: misplaced decimal points, corrupted rows, and obvious outliers that are unlikely to reflect real-world phenomena. To remove the most extreme of these, I used a z‑score based filter during ingestion (`app/main.py`). The z‑score for a value is (x - mean) / stddev; values with absolute z above a threshold are flagged as extreme. I chose the conventional threshold of 3.0 as a starting point because it balances false positives and false negatives for many natural distributions.

Concretely, the ingestion script reads the CSV files into a pandas DataFrame, coerces the target columns (temperature, salinity, ODO) to numeric types, computes per‑column mean and standard deviation, and marks any row as an outlier if any target measurement has |z| > 3. Rows flagged as outliers are removed; the remaining cleaned rows are written to `data/cleaned.csv` and inserted into MongoDB under `water_quality_data.asv_1`. The script prints counts for total rows, removed rows, and inserted rows so the cleaning aggressiveness can be audited.

This approach is intentionally simple and interpretable. Its strengths are speed and clarity — for obviously bad sensor readings it works well. Its limits are also important: z‑score assumes an approximately symmetric unimodal distribution and is a univariate method. When distributions are skewed, multimodal, or when contextual validity depends on multiple variables (e.g., temperature that is plausible only at certain locations or times), z‑score can either leave bad values in or incorrectly discard valid extremes. For skewed data, an IQR or median/MAD approach may be more robust; for more nuanced errors, rules informed by domain knowledge are appropriate.

Endpoint design and rationale

The API is intentionally modest in scope to serve the needs of the Streamlit client while remaining easy to reason about. Endpoints are grouped by function: health and metadata, observations (with filtering and pagination), statistics, and outlier detection.

GET /api/observations supports limit/skip pagination, exact date matching, inclusive date ranges, and numeric min/max filters for temperature, salinity, and ODO. A practical complication is that the dataset stored `date` as strings in `MM/DD/YY` format; for single‑date lookups the API performs a simple equality match, but for ranges it uses a MongoDB aggregation pipeline that normalizes the stored strings to a sortable ISO‑like format (YYYY‑MM‑DD) and then applies range filters. This hybrid approach keeps the common case (single date lookups) simple while still enabling correct range semantics.

GET /api/stats accepts a comma‑separated `fields` parameter and returns min/max/avg/stddev per field. The server computes these using MongoDB aggregation (`$group`) so the client avoids transferring large volumes of raw data. GET /api/outliers provides two methods (zscore, iqr) and returns the matching documents together with the statistics used to determine the outlier bounds. Where possible, the heavy lifting is pushed to the database to keep the client responsive.

What I learned

This project reinforced a few practical lessons. First, data format parity matters: a mismatch between client date formats and stored date strings caused subtle bugs early on. Canonicalizing dates at ingestion (or storing True Date objects) reduces these classes of problems. Second, simple statistical methods are often the right first step: z‑score cleaning removed obvious junk data quickly, but it’s not the end of the story — for production workflows I would combine robust statistics, domain rules, and targeted manual review. Third, Streamlit’s session state and widget APIs require careful use of keys and separation of canonical state and widget-bound state to avoid runtime exceptions. Finally, performing aggregation and filtering server‑side keeps the UI snappy and reduces bandwidth costs.

Concluding remarks and next steps

The current pipeline is a practical foundation for exploration and demonstration. If I were to continue this project I would prioritize two improvements: record dates as ISO/MongoDB Date objects at ingestion to simplify querying and indexing, and extend the statistics endpoint to include percentiles and counts (computed in the database). Adding indexes on frequently filtered fields and introducing a small suite of automated tests for the API would be the next steps toward production readiness.

Overall, the project demonstrates a compact, reproducible pipeline from raw CSVs to a usable, queryable dataset and a simple web UI that supports exploratory analysis and outlier investigation.

