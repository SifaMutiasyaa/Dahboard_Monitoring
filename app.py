import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os
import glob
import re

st.set_page_config(
    page_title="Monitoring Temperature & Humidity",
    layout="wide"
)

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# CSS lebih kaya
st.markdown("""
<style>
    .main {
        background-color: #f5f6fa;
    }
    .kpi-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: white;
        padding: 15px 10px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
        flex: 1;
        transition: all 0.2s;
        border-top: 4px solid #1f2c5c;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #555;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2c5c;
        margin: 5px 0;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #888;
    }
    .section-title {
        background: #1f2c5c;
        color: white;
        padding: 8px 20px;
        border-radius: 30px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
        letter-spacing: 0.5px;
    }
    .filter-container {
        background: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 20px;
    }
    .stSelectbox label {
        font-weight: 600;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

st.title("Dashboard Monitoring Temperature dan Humidity")

# ======================
# SIDEBAR (tetap sama)
# ======================
st.sidebar.header("Data Tersimpan")
saved_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
file_names = [os.path.basename(f) for f in saved_files]

if "file_checks" not in st.session_state:
    st.session_state.file_checks = {f: False for f in file_names}
else:
    for f in file_names:
        if f not in st.session_state.file_checks:
            st.session_state.file_checks[f] = False

for fname in file_names:
    st.session_state.file_checks[fname] = st.sidebar.checkbox(
        fname, value=st.session_state.file_checks.get(fname, False)
    )

if st.sidebar.button("Hapus Terpilih"):
    selected = [f for f, checked in st.session_state.file_checks.items() if checked]
    if selected:
        st.session_state.confirm_delete = True
        st.session_state.files_to_delete = selected
    else:
        st.sidebar.warning("Pilih minimal satu file.")

if st.session_state.get("confirm_delete", False):
    st.sidebar.warning(f"Anda yakin ingin menghapus {len(st.session_state.files_to_delete)} file?")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Ya, Hapus!"):
            for fname in st.session_state.files_to_delete:
                path = os.path.join(DATA_FOLDER, fname)
                if os.path.exists(path):
                    os.remove(path)
            st.session_state.confirm_delete = False
            st.session_state.files_to_delete = []
            for f in st.session_state.file_checks:
                st.session_state.file_checks[f] = False
            st.rerun()
    with col2:
        if st.button("Batal"):
            st.session_state.confirm_delete = False
            st.session_state.files_to_delete = []
            st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Upload Data Baru")
uploaded_files = st.sidebar.file_uploader(
    "Pilih File CSV", type="csv", accept_multiple_files=True
)
if st.sidebar.button("Simpan Data"):
    if uploaded_files:
        for file in uploaded_files:
            save_path = os.path.join(DATA_FOLDER, file.name)
            with open(save_path, "wb") as f:
                f.write(file.getbuffer())
        st.sidebar.success(f"{len(uploaded_files)} file berhasil disimpan")
        st.rerun()
    else:
        st.sidebar.warning("Tidak ada file yang dipilih.")

# ======================
# BACA CSV
# ======================
csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
if len(csv_files) == 0:
    st.info("Belum ada data. Silakan upload CSV di sidebar.")
    st.stop()

month_map_name = {
    'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6,
    'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12,
    'january':1, 'february':2, 'march':3, 'april':4, 'may':5, 'june':6,
    'july':7, 'august':8, 'september':9, 'october':10, 'november':11, 'december':12
}

def parse_date_from_components(date_str, year_str, month_str, day_str):
    if date_str and str(date_str).strip():
        for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%d-%b-%Y', '%b-%d-%Y']:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                pass
        try:
            return pd.to_datetime(date_str)
        except:
            pass
    year = parse_year(year_str)
    month = parse_month(month_str)
    day = parse_day(day_str)
    if year and month and day:
        try:
            return pd.to_datetime(f"{year}-{month}-{day}")
        except:
            pass
    return pd.NaT

def parse_year(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    match = re.search(r'\b(\d{4})\b', val_str)
    if match:
        return int(match.group(1))
    return None

def parse_month(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip().lower()
    match = re.search(r'\b(\d{1,2})\b', val_str)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 12:
            return num
    if val_str in month_map_name:
        return month_map_name[val_str]
    return None

def parse_day(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    match = re.search(r'\b(\d{1,2})\b', val_str)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 31:
            return num
    return None

temp_list = []
humi_list = []

for file in csv_files:
    raw = pd.read_csv(file, header=None)
    room_header = raw.iloc[1].fillna("")
    measure_header = raw.iloc[2].fillna("")
    data = raw.iloc[3:].reset_index(drop=True)

    temp_df = data.iloc[:, :4].copy()
    humi_df = data.iloc[:, :4].copy()
    temp_df.columns = ["Date","Year","Month","Week"]
    humi_df.columns = ["Date","Year","Month","Week"]

    for df in [temp_df, humi_df]:
        dates = []
        for idx, row in df.iterrows():
            dt = parse_date_from_components(row['Date'], row['Year'], row['Month'], row['Week'])
            dates.append(dt)
        df['DateObj'] = dates
        df['YearNum'] = df['DateObj'].dt.year
        df['MonthNum'] = df['DateObj'].dt.month
        df['DayNum'] = df['DateObj'].dt.day
        df.dropna(subset=['DateObj'], inplace=True)
        df['YearNum'] = df['YearNum'].astype(int)
        df['MonthNum'] = df['MonthNum'].astype(int)
        df['DayNum'] = df['DayNum'].astype(int)

    current_room = ""
    for col in range(4, len(measure_header)):
        room = str(room_header[col]).strip()
        measure = str(measure_header[col]).strip()
        if room:
            current_room = room
        if measure.lower().startswith("temp"):
            temp_df[current_room] = pd.to_numeric(data.iloc[:,col], errors="coerce")
        elif measure.lower().startswith("humi"):
            humi_df[current_room] = pd.to_numeric(data.iloc[:,col], errors="coerce")

    temp_list.append(temp_df)
    humi_list.append(humi_df)

if not temp_list:
    st.error("Tidak ada data suhu yang terbaca. Periksa format CSV.")
    with st.expander("Lihat data mentah (5 baris pertama)"):
        st.dataframe(raw.head())
    st.stop()

temp_master = pd.concat(temp_list, ignore_index=True)
humi_master = pd.concat(humi_list, ignore_index=True)

if temp_master.empty or humi_master.empty:
    st.warning("Tidak ada data yang valid. Pastikan tanggal bisa diparse.")
    with st.expander("Lihat data mentah (5 baris pertama)"):
        st.dataframe(raw.head())
    st.stop()

# ======================
# KONVERSI BULAN KE NAMA
# ======================
month_num_to_name = {
    1:"January",2:"February",3:"March",4:"April",
    5:"May",6:"June",7:"July",8:"August",
    9:"September",10:"October",11:"November",12:"December"
}
temp_master["MonthName"] = temp_master["MonthNum"].map(month_num_to_name)
humi_master["MonthName"] = humi_master["MonthNum"].map(month_num_to_name)

# ======================
# FILTER DROPDOWN TAHUN & BULAN (kembali ke semula)
# ======================
year_list = sorted(temp_master["YearNum"].unique())
selected_year = st.selectbox("Pilih Tahun", ["All"] + list(year_list))

month_order = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
available_months = [m for m in month_order if m in temp_master["MonthName"].dropna().unique()]
selected_month = st.selectbox("Pilih Bulan", ["All"] + available_months)

if selected_year != "All":
    temp_master = temp_master[temp_master["YearNum"] == selected_year]
    humi_master = humi_master[humi_master["YearNum"] == selected_year]

if selected_month != "All":
    temp_master = temp_master[temp_master["MonthName"] == selected_month]
    humi_master = humi_master[humi_master["MonthName"] == selected_month]

if temp_master.empty or humi_master.empty:
    st.warning("Belum ada data untuk filter yang dipilih.")
    st.stop()

# ======================
# KPI
# ======================
meta_cols = ["Date","Year","Month","Week","DateObj","YearNum","MonthNum","DayNum","MonthName"]
temp_cols = [c for c in temp_master.columns if c not in meta_cols]
humi_cols = [c for c in humi_master.columns if c not in meta_cols]

temp_stack = temp_master[temp_cols].stack()
avg_temp = round(temp_stack.mean(),2)
max_temp = round(temp_stack.max(),2)
min_temp = round(temp_stack.min(),2)
max_temp_loc = temp_stack.idxmax()[1]
min_temp_loc = temp_stack.idxmin()[1]

humi_stack = humi_master[humi_cols].stack()
avg_humi = round(humi_stack.mean(),2)
max_humi = round(humi_stack.max(),2)
min_humi = round(humi_stack.min(),2)
max_humi_loc = humi_stack.idxmax()[1]
min_humi_loc = humi_stack.idxmin()[1]

# Last Update
latest_file = max(csv_files, key=os.path.getmtime)
last_update = pd.to_datetime(os.path.getmtime(latest_file), unit="s").strftime("%d %B %Y %H:%M")
latest_file_name = os.path.basename(latest_file)

# ======================
# TAMPILAN KPI DENGAN CSS CARD
# ======================
st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">AVG TEMPERATURE</div>
        <div class="kpi-value">{avg_temp} °C</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">TEMP TERTINGGI VS TERENDAH</div>
        <div class="kpi-value">{max_temp} | {min_temp}</div>
        <div class="kpi-sub">{max_temp_loc} | {min_temp_loc}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">AVG HUMIDITY</div>
        <div class="kpi-value">{avg_humi}%</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">HUMI TERTINGGI VS TERENDAH</div>
        <div class="kpi-value">{max_humi} | {min_humi}</div>
        <div class="kpi-sub">{max_humi_loc} | {min_humi_loc}</div>
    </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">LAST UPDATE</div>
        <div class="kpi-value" style="font-size:1.2rem;">{last_update}</div>
        <div class="kpi-sub">{latest_file_name}</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ======================
# TEMPERATURE
# ======================
st.markdown('<div class="section-title">TEMPERATURE</div>', unsafe_allow_html=True)
left, right = st.columns([3,1])
with left:
    # Jika bulan = All -> agregasi per bulan; else per hari (seperti sebelumnya)
    if selected_month == "All" and not temp_master["MonthName"].dropna().empty:
        temp_agg = temp_master.groupby("MonthName", as_index=False)[temp_cols].mean()
        temp_agg["MonthName"] = pd.Categorical(
            temp_agg["MonthName"], categories=month_order, ordered=True
        )
        temp_agg = temp_agg.sort_values("MonthName")
        temp_long = temp_agg.melt(
            id_vars=["MonthName"], value_vars=temp_cols,
            var_name="Location", value_name="Temperature"
        )
        x_axis = "MonthName"
    else:
        temp_long = temp_master.melt(
            id_vars=["DayNum"], value_vars=temp_cols,
            var_name="Location", value_name="Temperature"
        )
        x_axis = "DayNum"
    fig_temp = px.line(temp_long, x=x_axis, y="Temperature", color="Location")
    fig_temp.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with right:
    # urutkan berdasarkan rata-rata tertinggi
    temp_summary = pd.DataFrame({
        "Location": temp_cols,
        "Avg": [round(temp_master[c].mean(),2) for c in temp_cols],
        "Max": [round(temp_master[c].max(),2) for c in temp_cols],
        "Min": [round(temp_master[c].min(),2) for c in temp_cols]
    }).sort_values("Avg", ascending=False)
    st.dataframe(temp_summary, height=400, use_container_width=True)

# ======================
# HUMIDITY
# ======================
st.markdown('<div class="section-title">HUMIDITY</div>', unsafe_allow_html=True)
left, right = st.columns([3,1])
with left:
    if selected_month == "All" and not humi_master["MonthName"].dropna().empty:
        humi_agg = humi_master.groupby("MonthName", as_index=False)[humi_cols].mean()
        humi_agg["MonthName"] = pd.Categorical(
            humi_agg["MonthName"], categories=month_order, ordered=True
        )
        humi_agg = humi_agg.sort_values("MonthName")
        humi_long = humi_agg.melt(
            id_vars=["MonthName"], value_vars=humi_cols,
            var_name="Location", value_name="Humidity"
        )
        x_axis = "MonthName"
    else:
        humi_long = humi_master.melt(
            id_vars=["DayNum"], value_vars=humi_cols,
            var_name="Location", value_name="Humidity"
        )
        x_axis = "DayNum"
    fig_humi = px.line(humi_long, x=x_axis, y="Humidity", color="Location")
    fig_humi.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_humi, use_container_width=True)

with right:
    humi_summary = pd.DataFrame({
        "Location": humi_cols,
        "Avg": [round(humi_master[c].mean(),2) for c in humi_cols],
        "Max": [round(humi_master[c].max(),2) for c in humi_cols],
        "Min": [round(humi_master[c].min(),2) for c in humi_cols]
    }).sort_values("Avg", ascending=False)
    st.dataframe(humi_summary, height=400, use_container_width=True)

# ======================
# DOWNLOAD
# ======================
output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    temp_master.to_excel(writer, sheet_name="Temperature", index=False)
    humi_master.to_excel(writer, sheet_name="Humidity", index=False)
    temp_summary.to_excel(writer, sheet_name="Temperature Summary", index=False)
    humi_summary.to_excel(writer, sheet_name="Humidity Summary", index=False)

st.download_button(
    label="Download Monitoring Report",
    data=output.getvalue(),
    file_name="monitoring_site.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)