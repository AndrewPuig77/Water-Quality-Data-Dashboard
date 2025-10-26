import streamlit as st
import pandas as pd 
import plotly.express as px
import plotly.graph_objects as go
import requests
import math
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

# API base URL
API_BASE = "http://127.0.0.1:5000/api"

# Title
st.title("🌊 Water Quality Data Dashboard")

# Sidebar Controls
st.sidebar.title("Control Panel")

# Probe server for available fields by fetching a single observation
available_fields = ["temperature", "salinity", "odo", "date"]
try:
    probe = requests.get(f"{API_BASE}/observations", params={"limit": 1}, timeout=5)
    if probe.status_code == 200:
        probe_items = probe.json().get("items", [])
        if probe_items:
            available_fields = sorted(list(probe_items[0].keys()))
except Exception:
    pass

# Date filtering
st.sidebar.subheader("Date Filter")
date_mode = st.sidebar.radio("Mode", ["Single Date", "Date Range"], index=0, key="date_mode")

# Initialize filter variables
date_filter = None
single_date = None
start_date = None
end_date = None

if date_mode == "Single Date":
    single_date = st.sidebar.date_input("Select date", key="single_date")
    if single_date:
        # send 2-digit year to match DB format
        date_filter = single_date.strftime("%m/%d/%y")
elif date_mode == "Date Range":
    date_range = st.sidebar.date_input(
        "Select start and end dates", 
        value=(datetime.today() - timedelta(days=7), datetime.today()), 
        key="date_range"
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
        # we'll send start_date and end_date separately to API
        date_filter = None

# Temperature range
st.sidebar.subheader("Temperature (°C)")
temp_min = st.sidebar.number_input("Min Temp", value=None, format="%.2f", key="temp_min")
temp_max = st.sidebar.number_input("Max Temp", value=None, format="%.2f", key="temp_max")

# Salinity range
st.sidebar.subheader("Salinity (ppt)")
sal_min = st.sidebar.number_input("Min Salinity", value=None, format="%.2f", key="sal_min")
sal_max = st.sidebar.number_input("Max Salinity", value=None, format="%.2f", key="sal_max")

# ODO range
st.sidebar.subheader("ODO (mg/L)")
odo_min = st.sidebar.number_input("Min ODO", value=None, format="%.2f", key="odo_min")
odo_max = st.sidebar.number_input("Max ODO", value=None, format="%.2f", key="odo_max")

# Pagination
st.sidebar.subheader("Pagination")
limit = st.sidebar.slider("Limit", min_value=100, max_value=1000, value=100, step=10)
# Ensure a session_state key for pagination exists before creating widgets
if "skip" not in st.session_state:
    st.session_state["skip"] = 0

def _on_skip_input_changed():
    # Copy the widget value into the canonical skip session key
    st.session_state["skip"] = int(st.session_state.get("skip_input", 0))

# Manual Skip input (safe key 'skip_input'); step by page size for convenience
skip_input = st.sidebar.number_input(
    "Skip (offset)", min_value=0, value=st.session_state["skip"], step=limit, key="skip_input",
    on_change=_on_skip_input_changed
)
# Use canonical skip
skip = st.session_state["skip"]

st.sidebar.divider()

# Apply filters button
col1 = st.sidebar.container()
with col1:
    apply_filters = st.button("🔍 Apply Filters", type="primary", use_container_width=True)

# Show active filters
active_filters = []
if date_mode == "Single Date" and single_date:
    active_filters.append(f"📅 Date: {single_date.strftime('%m/%d/%y')}")
elif date_mode == "Date Range" and start_date and end_date:
    active_filters.append(f"📅 Range: {start_date.strftime('%m/%d/%y')} → {end_date.strftime('%m/%d/%y')}")
if temp_min is not None or temp_max is not None:
    active_filters.append(f"🌡️ Temp: {temp_min or 'Min'} - {temp_max or 'Max'} °C")
if sal_min is not None or sal_max is not None:
    active_filters.append(f"🧂 Salinity: {sal_min or 'Min'} - {sal_max or 'Max'} ppt")
if odo_min is not None or odo_max is not None:
    active_filters.append(f"💨 ODO: {odo_min or 'Min'} - {odo_max or 'Max'} mg/L")

if active_filters:
    st.info("**Active Filters:** " + " | ".join(active_filters))
else:
    st.info("**No filters applied** - Showing all data")

# Build query parameters
params = {"limit": limit, "skip": skip}
if date_mode == "Single Date" and single_date is not None:
    params["date"] = single_date.strftime("%m/%d/%y")
elif date_mode == "Date Range" and start_date is not None and end_date is not None:
    # server expects 'date_start' / 'date_end'
    params["date_start"] = start_date.strftime("%m/%d/%y")
    params["date_end"] = end_date.strftime("%m/%d/%y")
if temp_min is not None:
    params["min_temp"] = temp_min
if temp_max is not None:
    params["max_temp"] = temp_max
if sal_min is not None:
    params["min_sal"] = sal_min
if sal_max is not None:
    params["max_sal"] = sal_max
if odo_min is not None:
    params["min_odo"] = odo_min
if odo_max is not None:
    params["max_odo"] = odo_max

# Debug info (helps verify pagination behavior)
with st.sidebar.expander("Debug (request params)", expanded=False):
    st.write("limit:", limit)
    st.write("skip (session):", st.session_state.get("skip"))
    st.write("params:", params)

# Fetch data from API
try:
    response = requests.get(f"{API_BASE}/observations", params=params, timeout=50)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        total_count = data.get("count", 0)
        
        # Display counts and pagination
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Matching Records", total_count)
        with col2:
            st.metric("Returned Records", len(items))

        # Compute pagination
        total_pages = math.ceil(total_count / limit) if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        with col3:
            st.metric("Page", f"{current_page} / {total_pages}")

        # Prev / Next buttons for navigation using callbacks (no experimental_rerun)
        def go_prev(limit_val=limit):
            st.session_state["skip"] = max(0, st.session_state.get("skip", 0) - limit_val)

        def go_next(limit_val=limit, total_pages_val=total_pages):
            st.session_state["skip"] = min(max(0, (total_pages_val - 1) * limit_val), st.session_state.get("skip", 0) + limit_val)

        nav_col1, nav_col2 = st.columns([1, 1])
        with nav_col1:
            st.button("◀ Prev", on_click=go_prev)
        with nav_col2:
            st.button("Next ▶", on_click=go_next)
        
        if items:
            df = pd.DataFrame(items)
            
            # Keep original date format, create datetime column for sorting/plotting
            if "date" in df.columns:
                # Store original date strings for display
                df["date_display"] = df["date"]
                
                # Try to parse dates for sorting (but keep original for display)
                try:
                    # Parse MM/DD/YY format - try both with leading zeros and without
                    df["date_dt"] = pd.to_datetime(df["date"], format='%m/%d/%y', errors='coerce')
                    # If that fails, try without strict formatting
                    if df["date_dt"].isna().all():
                        df["date_dt"] = pd.to_datetime(df["date"], errors='coerce')
                except:
                    df["date_dt"] = pd.to_datetime(df["date"], errors='coerce')

            # Data Table
            st.subheader("Observations Data")

            # Show key columns first - use date_display to show original format
            display_cols = ["date", "Time", "latitude", "longitude", "temperature", "salinity", "odo"]
            available_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[available_cols], use_container_width=True, height=300)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="water_quality_data.csv",
                mime="text/csv"
            )
            
            # Visualizations
            st.subheader("Visualizations")
            
            # Create tabs for different charts
            tab1, tab2, tab3, tab4 = st.tabs(["Temperature Over Time", "Salinity Distribution", "Temp vs Salinity", "Map View"])
            
            with tab1:
                # Line chart - Temperature over time
                if "temperature" in df.columns and "date_dt" in df.columns:
                    # Sort by datetime for proper time series
                    df_sorted = df.dropna(subset=["date_dt"]).sort_values("date_dt")
                    if len(df_sorted) > 0:
                        fig1 = px.line(df_sorted, x="date_dt", y="temperature", 
                                      title="Temperature Over Time",
                                      labels={"temperature": "Temperature (°C)", "date_dt": "Date"})
                        fig1.update_traces(line_color='#FF6B6B')
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.warning("No valid date/temperature data for plotting")
                elif "temperature" in df.columns:
                    # Fallback: plot by index
                    df_sorted = df.sort_index()
                    fig1 = px.line(df_sorted, y="temperature", 
                                  title="Temperature Over Time",
                                  labels={"temperature": "Temperature (°C)", "index": "Record Index"})
                    fig1.update_traces(line_color='#FF6B6B')
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("Temperature data not available")
            
            with tab2:
                # Histogram - Salinity distribution
                if "salinity" in df.columns:
                    fig2 = px.histogram(df, x="salinity", nbins=30,
                                       title="Salinity Distribution",
                                       labels={"salinity": "Salinity (ppt)", "count": "Frequency"})
                    fig2.update_traces(marker_color='#4ECDC4')
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("Salinity data not available")
            
            with tab3:
                # Scatter plot - Temperature vs Salinity colored by ODO
                if all(col in df.columns for col in ["temperature", "salinity", "odo"]):
                    fig3 = px.scatter(df, x="temperature", y="salinity", color="odo",
                                     title="Temperature vs Salinity (colored by ODO)",
                                     labels={"temperature": "Temperature (°C)", 
                                            "salinity": "Salinity (ppt)",
                                            "odo": "ODO (mg/L)"},
                                     color_continuous_scale="Viridis")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.warning("Required data not available for scatter plot")
            
            with tab4:
                # Map view
                if all(col in df.columns for col in ["latitude", "longitude"]):
                    fig4 = px.scatter_mapbox(df, lat="latitude", lon="longitude",
                                            hover_data=["temperature", "salinity", "odo", "date"],
                                            color="temperature",
                                            size_max=15,
                                            zoom=10,
                                            title="Observation Locations")
                    fig4.update_layout(mapbox_style="open-street-map")
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.warning("Location data not available")
        
        else:
            st.warning("No observations found with the current filters.")
    
    else:
        st.error(f"API request failed with status code {response.status_code}")
        st.write("Response:", response.text)

except requests.exceptions.RequestException as e:
    st.error(f"Failed to connect to API: {e}")
    st.info("Make sure your Flask API is running at http://127.0.0.1:5000")

# Statistics Panel
st.divider()
st.subheader("Summary Statistics")

# Let the user choose which fields to show stats for
stats_fields = st.multiselect("Fields for summary statistics", options=available_fields, default=[f for f in ["temperature", "salinity", "odo"] if f in available_fields])
if stats_fields:
    try:
        stats_response = requests.get(f"{API_BASE}/stats", params={"fields": ",".join(stats_fields)}, timeout=50)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            cols = st.columns(len(stats_fields))
            for i, field in enumerate(stats_fields):
                with cols[i]:
                    st.markdown(f"**{field}**")
                    fstats = stats.get(field, {})
                    if fstats and fstats.get("min") is not None:
                        st.write(f"Min: {fstats['min']}")
                        st.write(f"Max: {fstats['max']}")
                        st.write(f"Avg: {fstats['avg']}")
                        st.write(f"Std Dev: {fstats['stddev']}")
                    else:
                        st.write("No data available")
        else:
            st.error("Failed to fetch statistics")
    except Exception as e:
        st.error(f"Error fetching stats: {e}")

# Outliers Panel
st.divider()
st.subheader("Outlier Detection")

col1, col2, col3 = st.columns(3)
with col1:
    outlier_field = st.selectbox("Field", options=available_fields, index=0 if "temperature" in available_fields else 0, key="outlier_field")
with col2:
    outlier_method = st.selectbox("Method", ["zscore", "iqr"], key="outlier_method")
with col3:
    outlier_k = st.number_input("K value", value=3.0 if outlier_method == "zscore" else 1.5, step=0.1, format="%.2f", key="outlier_k")

if st.button("Detect Outliers", key="detect_outliers_btn"):
    try:
        outlier_params = {"field": outlier_field, "method": outlier_method, "k": outlier_k}
        outlier_response = requests.get(f"{API_BASE}/outliers", params=outlier_params, timeout=50)
        
        if outlier_response.status_code == 200:
            outlier_data = outlier_response.json()
            outlier_count = outlier_data.get("count", 0)
            outliers = outlier_data.get("outliers", [])
            
            st.metric("Outliers Found", outlier_count)
            
            # Show statistics used for detection
            if "statistics" in outlier_data:
                stats = outlier_data["statistics"]
                if outlier_method == "zscore":
                    if stats.get('mean') is not None and stats.get('stddev') is not None:
                        st.info(f"**Detection Statistics:** Mean: {stats.get('mean'):.2f}, Std Dev: {stats.get('stddev'):.2f}")
                else:
                    if all(k in stats for k in ['q1', 'q3', 'iqr']):
                        st.info(f"**Detection Statistics:** Q1: {stats.get('q1'):.2f}, Q3: {stats.get('q3'):.2f}, IQR: {stats.get('iqr'):.2f}")
                        st.write(f"Bounds: [{stats.get('lower_bound'):.2f}, {stats.get('upper_bound'):.2f}]")
            
            if outliers:
                outlier_df = pd.DataFrame(outliers)
                # Use lowercase 'date' (matches your database field)
                display_cols = [outlier_field, "latitude", "longitude", "date"]
                if outlier_method == "zscore" and "z_score" in outlier_df.columns:
                    display_cols.append("z_score")
                available = [col for col in display_cols if col in outlier_df.columns]
                st.dataframe(outlier_df[available], use_container_width=True)
                
                # Download outliers button
                outlier_csv = outlier_df.to_csv(index=False)
                st.download_button(
                    label="Download Outliers as CSV",
                    data=outlier_csv,
                    file_name=f"outliers_{outlier_field}_{outlier_method}.csv",
                    mime="text/csv",
                    key="download_outliers"
                )
            else:
                st.success("No outliers detected with current parameters!")
        else:
            st.error(f"Failed to fetch outliers: Status {outlier_response.status_code}")
            try:
                error_data = outlier_response.json()
                st.error(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                st.error(f"Response: {outlier_response.text}")
    except Exception as e:
        st.error(f"Error detecting outliers: {type(e).__name__}: {e}")