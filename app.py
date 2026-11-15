from pathlib import Path
import copy
import json
import re
import unicodedata
import base64

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="EWS Ketahanan Pangan Jawa Timur",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CSV_PATH = DATA_DIR / "EWS_Dashboard_Gabungan_2018_2025Q1.csv"
GEOJSON_PATH = DATA_DIR / "Batas_Kabupaten_Kota_Jawa_Timur.geojson"

# Asset visual dashboard. Nama file mengikuti file asli yang dikirim pengguna.
ASSET_DIR = BASE_DIR / "assets"
BACKGROUND_PATH = ASSET_DIR / "background_sawah.jpg.jfif"
LOGO_JATIM_PATH = ASSET_DIR / "logo_jatim.jfif"
LOGO_BPS_PATH = ASSET_DIR / "logo_bps_jatim.jfif"
LOGO_TELKOM_PATH = ASSET_DIR / "logo_telkom.jfif"


def image_data_uri(path):
    """Baca gambar lokal sebagai data URI agar aman ditampilkan di Streamlit."""
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in {".jfif", ".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


BACKGROUND_URI = image_data_uri(BACKGROUND_PATH)
LOGO_JATIM_URI = image_data_uri(LOGO_JATIM_PATH)
LOGO_BPS_URI = image_data_uri(LOGO_BPS_PATH)
LOGO_TELKOM_URI = image_data_uri(LOGO_TELKOM_PATH)

STATUS_COLORS = {
    "Aman": "#35B77A",
    "Waspada": "#E8B949",
    "Kritis": "#F06464",
    "Tidak tersedia": "#B8BEC7",
}

MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}
MONTH_SHORT = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
}


# ============================================================
# CSS — DARK GREEN GLASSMORPHISM / AGRICULTURE COMMAND CENTER
# ============================================================

DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --forest: #071f17;
    --forest-2: #0b3022;
    --emerald: #2f9b68;
    --emerald-bright: #55d69a;
    --rice-gold: #d8b45a;
    --text-main: #f3f8f2;
    --text-soft: #c2d4c8;
    --glass: rgba(9, 43, 29, 0.66);
    --glass-strong: rgba(6, 32, 22, 0.82);
    --glass-border: rgba(215, 235, 218, 0.17);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
}

.stApp {
    color: var(--text-main);
    background-color: #061b14;
    background-image:
        linear-gradient(115deg, rgba(3, 20, 14, 0.91) 0%, rgba(5, 31, 21, 0.80) 48%, rgba(4, 24, 17, 0.90) 100%),
        url("__BACKGROUND_IMAGE__");
    background-size: cover;
    background-position: center center;
    background-attachment: fixed;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main,
.block-container {
    background: transparent !important;
}

[data-testid="stHeader"] {
    background: rgba(4, 25, 17, 0.58) !important;
    backdrop-filter: blur(16px);
}

[data-testid="stToolbar"] {
    right: 1rem;
}

.main .block-container {
    max-width: 1600px;
    padding-top: 1.35rem;
    padding-bottom: 2.5rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(4, 29, 20, 0.96), rgba(7, 39, 27, 0.91)) !important;
    border-right: 1px solid rgba(218, 238, 219, 0.15);
    backdrop-filter: blur(24px);
}

[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
}

[data-testid="stSidebar"] * {
    color: #e9f3eb;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: #b9cec0 !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] > div > div {
    background: rgba(237, 247, 239, 0.09) !important;
    border: 1px solid rgba(219, 238, 222, 0.22) !important;
    border-radius: 11px !important;
    color: #f3f8f2 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] input {
    color: #f3f8f2 !important;
}

[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #d5e6d9 !important;
    font-weight: 600;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 4px 18px 4px;
    margin-bottom: 14px;
    border-bottom: 1px solid rgba(222, 239, 225, 0.14);
}
.sidebar-brand img {
    width: 54px;
    height: 54px;
    object-fit: contain;
    border-radius: 13px;
    background: rgba(255,255,255,0.96);
    padding: 4px;
}
.sidebar-brand .brand-title {
    color: #f5f8ef;
    font-weight: 800;
    font-size: 1.03rem;
    line-height: 1.25;
}
.sidebar-brand .brand-sub {
    color: #b6cdbd;
    font-size: 0.70rem;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    margin-top: 4px;
}

.hero-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 20px 23px;
    margin: 0 0 18px 0;
    border: 1px solid rgba(224, 241, 225, 0.20);
    border-radius: 20px;
    background: linear-gradient(110deg, rgba(5, 39, 26, 0.83), rgba(14, 65, 42, 0.57));
    box-shadow: 0 16px 44px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.10);
    backdrop-filter: blur(20px);
}
.hero-main {
    display: flex;
    align-items: center;
    gap: 17px;
    min-width: 0;
}
.hero-seal {
    width: 84px;
    height: 84px;
    object-fit: contain;
    border-radius: 17px;
    background: rgba(255,255,255,0.98);
    padding: 3px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.20);
    flex: 0 0 auto;
}
.hero-kicker {
    color: #e2c878;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 1.7px;
    text-transform: uppercase;
    margin-bottom: 5px;
}
.main-title {
    font-size: clamp(1.35rem, 2.5vw, 2.05rem);
    font-weight: 800;
    color: #f6fbf4;
    letter-spacing: -0.65px;
    line-height: 1.15;
    margin: 0;
}
.main-subtitle {
    color: #c4d8c9;
    font-size: 0.87rem;
    margin-top: 7px;
}
.hero-logos {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}
.logo-chip {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    padding: 3px;
    border-radius: 16px;
    background: rgba(255,255,255,0.98);
    border: 1px solid rgba(255,255,255,0.78);
    box-shadow: 0 7px 20px rgba(0,0,0,0.18);
    overflow: hidden;
}
.logo-chip img {
    display: block;
    width: 108%;
    height: 108%;
    max-width: none;
    max-height: none;
    object-fit: contain;
    flex: 0 0 auto;
}

.metric-card {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, rgba(19, 75, 49, 0.72), rgba(6, 38, 26, 0.72));
    border: 1px solid rgba(220, 240, 222, 0.20);
    border-radius: 17px;
    padding: 17px 14px 14px 14px;
    text-align: center;
    min-height: 122px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.20), inset 0 1px 0 rgba(255,255,255,0.10);
    backdrop-filter: blur(18px);
}
.metric-card:before {
    content: "";
    position: absolute;
    top: 0;
    left: 16%;
    width: 68%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(226,200,120,0.9), transparent);
}
.metric-label {
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 1.25px;
    margin-bottom: 5px;
}
.metric-value {
    font-size: 2.25rem;
    line-height: 1.15;
    font-weight: 800;
    margin: 3px 0;
    text-shadow: 0 0 18px rgba(255,255,255,0.10);
}
.metric-caption {
    color: #c1d5c7;
    font-size: 0.74rem;
}

.panel {
    background: var(--glass);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 11px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.17), inset 0 1px 0 rgba(255,255,255,0.08);
    backdrop-filter: blur(18px);
}
.panel-title {
    font-weight: 800;
    color: #f1f7ef;
    font-size: 0.96rem;
    letter-spacing: 0.1px;
    margin-bottom: 10px;
}
.detail-row {
    display: grid;
    grid-template-columns: 1.3fr 18px 2fr;
    gap: 7px;
    font-size: 0.82rem;
    padding: 5px 0;
    color: #c9dace;
    border-bottom: 1px solid rgba(226, 241, 227, 0.07);
}
.detail-row:last-child { border-bottom: 0; }
.detail-value {
    font-weight: 650;
    color: #f1f7ef;
}
.status-pill {
    display: inline-block;
    border-radius: 7px;
    padding: 5px 11px;
    font-weight: 800;
    font-size: 0.76rem;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}
.small-muted {
    color: #b9cec0;
    font-size: 0.76rem;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
.stCaption,
label {
    color: #d2e2d6;
}
[data-testid="stAlert"] {
    background: rgba(17, 69, 45, 0.72) !important;
    border: 1px solid rgba(219, 239, 220, 0.20) !important;
    color: #eef8ef !important;
    border-radius: 13px !important;
}
[data-testid="stAlert"] p { color: #eef8ef !important; }


[data-testid="stSpinner"] {
    display: inline-flex;
    align-items: center;
    padding: 12px 16px;
    background: rgba(8, 49, 32, 0.90) !important;
    border: 1px solid rgba(151, 218, 174, 0.34);
    border-radius: 13px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.08);
    backdrop-filter: blur(16px);
}
[data-testid="stSpinner"] p {
    color: #EAF7EC !important;
    font-weight: 650 !important;
    letter-spacing: 0.1px;
}
[data-testid="stSpinner"] svg {
    color: #91D7AA !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid rgba(190, 220, 199, 0.72);
    border-radius: 13px;
    overflow: hidden;
    background: rgba(237, 247, 239, 0.96);
    box-shadow: 0 10px 26px rgba(0,0,0,0.17);
}
div[data-testid="stPlotlyChart"] {
    background: rgba(7, 39, 27, 0.58);
    border: 1px solid rgba(220, 240, 222, 0.17);
    border-radius: 16px;
    padding: 7px 9px 0 9px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}
iframe[title*="streamlit_folium"] {
    border: 1px solid rgba(220, 240, 222, 0.20) !important;
    border-radius: 17px !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.22);
}
hr {
    border-color: rgba(225, 241, 226, 0.16) !important;
}
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #1f8155, #145b3b);
    color: #f5fbf5;
    border: 1px solid rgba(223, 242, 225, 0.22);
    border-radius: 10px;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #d8b45a;
    color: #ffffff;
    box-shadow: 0 0 18px rgba(216,180,90,0.20);
}
footer {visibility: hidden;}
</style>
"""
if BACKGROUND_URI:
    DASHBOARD_CSS = DASHBOARD_CSS.replace("__BACKGROUND_IMAGE__", BACKGROUND_URI)
else:
    DASHBOARD_CSS = DASHBOARD_CSS.replace("__BACKGROUND_IMAGE__", "")
st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


# ============================================================
# FUNGSI BANTU
# ============================================================

def normalize_name(value):
    """Samakan nama wilayah untuk pencocokan CSV dan GeoJSON."""
    s = unicodedata.normalize("NFKD", str(value))
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.strip().lower()
    s = re.sub(r"[_-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^kabupaten\s+", "", s)
    s = re.sub(r"^kab\.?\s+", "", s)
    s = re.sub(r"^provinsi\s+", "", s)
    return s.strip()


def fmt_number(value, decimals=2):
    if pd.isna(value):
        return "—"
    return (
        f"{float(value):,.{decimals}f}"
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


def fmt_ton(value, decimals=0):
    if pd.isna(value):
        return "—"
    return f"{fmt_number(value, decimals)} ton"


def classify_fsr(value):
    if pd.isna(value):
        return "Tidak tersedia"
    if value < 1.0:
        return "Kritis"
    if value < 1.2:
        return "Waspada"
    return "Aman"


def metric_card(label, value, color, caption="Kabupaten/Kota"):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label" style="color:{color}">{label.upper()}</div>
            <div class="metric-value" style="color:{color}">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_dashboard(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
    else:
        return None

    required = [
        "Kabupaten_Kota", "Wilayah_Key", "Tanggal", "Tahun", "Bulan",
        "Produksi_Padi_Ton_GKG", "Food_Availability_Ton",
        "Food_Requirement_Ton_Bulan", "FSR",
        "Status_Ketahanan_Pangan", "Tipe_Data",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            "Kolom wajib tidak ditemukan dalam CSV: " + ", ".join(missing)
        )

    df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")
    df["Bulan"] = pd.to_numeric(df["Bulan"], errors="coerce")
    df["Wilayah_Key"] = df["Wilayah_Key"].astype(str).str.strip().str.lower()
    df["Kabupaten_Kota"] = df["Kabupaten_Kota"].astype(str).str.strip()
    df["Tipe_Data"] = df["Tipe_Data"].astype(str).str.upper()

    numeric_cols = [
        "Produksi_Padi_Ton_GKG",
        "Food_Availability_Ton",
        "Food_Requirement_Ton_Bulan",
        "FSR",
        "Probabilitas_Defisit_Persen",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Tahun", "Bulan", "Wilayah_Key"]).copy()
    df["Tahun"] = df["Tahun"].astype(int)
    df["Bulan"] = df["Bulan"].astype(int)

    if "Probabilitas_Defisit_Persen" not in df.columns:
        df["Probabilitas_Defisit_Persen"] = np.nan

    if "Nama_Bulan" not in df.columns:
        df["Nama_Bulan"] = df["Bulan"].map(MONTH_NAMES)

    return df


def load_geojson(uploaded_file=None):
    if uploaded_file is not None:
        return json.load(uploaded_file)
    if GEOJSON_PATH.exists():
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def build_map(period_df, geojson_raw):
    """Membuat peta Folium dan menggabungkan data EWS ke batas wilayah."""
    if not geojson_raw:
        return None, 0

    name_to_key = {}
    for _, row in period_df.iterrows():
        name_to_key[normalize_name(row["Kabupaten_Kota"])] = row["Wilayah_Key"]

    rows_by_key = period_df.set_index("Wilayah_Key").to_dict(orient="index")
    geo = copy.deepcopy(geojson_raw)
    matched_features = []

    for feature in geo.get("features", []):
        props = feature.setdefault("properties", {})
        name = (
            props.get("WADMKK")
            or props.get("NAMOBJ")
            or props.get("NAME_2")
            or props.get("name")
        )
        if not name:
            continue

        key = name_to_key.get(normalize_name(name))
        if key is None or key not in rows_by_key:
            continue

        row = rows_by_key[key]
        status = str(row.get("Status_Ketahanan_Pangan", "Tidak tersedia"))
        if status not in STATUS_COLORS:
            status = "Tidak tersedia"

        props["_wilayah_key_ews"] = key
        props["_nama_wilayah_ews"] = str(row["Kabupaten_Kota"])
        props["_status_ews"] = status
        props["_fsr_ews"] = fmt_number(row.get("FSR"), 3)
        props["_produksi_ews"] = fmt_number(
            row.get("Produksi_Padi_Ton_GKG"), 2
        )
        prob = row.get("Probabilitas_Defisit_Persen")
        props["_prob_ews"] = (
            fmt_number(prob, 2) + "%"
            if pd.notna(prob)
            else "Tidak tersedia (historis)"
        )
        matched_features.append(feature)

    geo["features"] = matched_features

    if not matched_features:
        return None, 0

    m = folium.Map(
        location=[-7.7, 112.5],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    def style_function(feature):
        status = feature["properties"].get("_status_ews", "Tidak tersedia")
        return {
            "fillColor": STATUS_COLORS.get(status, STATUS_COLORS["Tidak tersedia"]),
            "color": "#FFFFFF",
            "weight": 1.0,
            "fillOpacity": 0.78,
        }

    def highlight_function(feature):
        return {
            "weight": 2.5,
            "color": "#263238",
            "fillOpacity": 0.95,
        }

    folium.GeoJson(
        geo,
        name="Status Ketahanan Pangan",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "_nama_wilayah_ews", "_status_ews", "_fsr_ews",
                "_produksi_ews", "_prob_ews",
            ],
            aliases=[
                "Kabupaten/Kota:",
                "Status:",
                "FSR:",
                "Produksi padi (ton GKG):",
                "Probabilitas defisit:",
            ],
            sticky=False,
            labels=True,
        ),
    ).add_to(m)

    legend_html = """
    <div style="
        position: fixed; bottom: 22px; left: 22px; z-index: 9999;
        background: rgba(5, 30, 21, .91); color: #edf7ee;
        padding: 11px 14px; border: 1px solid rgba(220,240,222,.28);
        border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,.30);
        backdrop-filter: blur(12px);
        font-size: 12px; line-height: 1.75;">
        <b style="letter-spacing:.6px;">STATUS KETAHANAN PANGAN</b><br>
        <span style="color:#55d69a;">■</span> Aman (FSR ≥ 1,20)<br>
        <span style="color:#f4c95d;">■</span> Waspada (1,00 ≤ FSR &lt; 1,20)<br>
        <span style="color:#ff7474;">■</span> Kritis (FSR &lt; 1,00)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    m.fit_bounds([[-8.9, 110.7], [-5.0, 114.7]])
    return m, len(matched_features)


def aggregate_period(data):
    """Agregat provinsi: jumlah FA / jumlah FR, bukan rata-rata FSR."""
    n_regions = data["Wilayah_Key"].nunique()
    fa = data["Food_Availability_Ton"].sum(min_count=1)
    fr = data["Food_Requirement_Ton_Bulan"].sum(min_count=1)
    gkg = data["Produksi_Padi_Ton_GKG"].sum(min_count=1)
    fsr = fa / fr if pd.notna(fr) and fr > 0 else np.nan
    saldo = fa - fr if pd.notna(fa) and pd.notna(fr) else np.nan
    return {
        "n_regions": n_regions,
        "fa": fa,
        "fr": fr,
        "gkg": gkg,
        "fsr": fsr,
        "saldo": saldo,
        "status": classify_fsr(fsr),
    }


def aggregate_by_region(data):
    """Agregasi multi-bulan per kabupaten/kota; FSR = total FA / total FR."""
    grouped = (
        data.groupby(["Wilayah_Key", "Kabupaten_Kota"], as_index=False)
        .agg(
            Produksi_Padi_Ton_GKG=("Produksi_Padi_Ton_GKG", "sum"),
            Food_Availability_Ton=("Food_Availability_Ton", "sum"),
            Food_Requirement_Ton_Bulan=("Food_Requirement_Ton_Bulan", "sum"),
        )
    )
    grouped["FSR"] = np.where(
        grouped["Food_Requirement_Ton_Bulan"] > 0,
        grouped["Food_Availability_Ton"] / grouped["Food_Requirement_Ton_Bulan"],
        np.nan,
    )
    grouped["Status_Ketahanan_Pangan"] = grouped["FSR"].apply(classify_fsr)
    # Probabilitas multi-bulan tidak boleh dihitung dengan menjumlahkan atau
    # merata-ratakan probabilitas bulanan.
    grouped["Probabilitas_Defisit_Persen"] = np.nan
    grouped["Tipe_Data"] = (
        "FORECAST" if (data["Tipe_Data"].str.upper() == "FORECAST").any()
        else "HISTORIS"
    )
    return grouped


# ============================================================
# SIDEBAR DAN PEMUATAN DATA
# ============================================================

st.sidebar.markdown(
    f"""
    <div class="sidebar-brand">
        {"<img src='" + LOGO_JATIM_URI + "' alt='Logo Jawa Timur'>" if LOGO_JATIM_URI else ""}
        <div>
            <div class="brand-title">EWS Pangan<br>Jawa Timur</div>
            <div class="brand-sub">Pemantauan Ketahanan Pangan</div>
        </div>
    </div>
    <div style="color:#bdd2c3;font-size:0.78rem;line-height:1.55;margin-bottom:18px;">
        Sistem peringatan dini ketahanan pangan berbasis produksi padi.
    </div>
    """,
    unsafe_allow_html=True,
)

# Dataset dibaca otomatis dari folder data. Komponen upload hanya muncul
# sebagai cadangan jika file lokal belum tersedia.
uploaded_csv = None
uploaded_geojson = None

if not CSV_PATH.exists() or not GEOJSON_PATH.exists():
    with st.sidebar.expander("Unggah data (hanya jika file belum ada)", expanded=True):
        if not CSV_PATH.exists():
            uploaded_csv = st.file_uploader(
                "Upload CSV dashboard",
                type=["csv"],
                help="File akan digunakan sebagai sumber data untuk sesi aplikasi ini.",
            )
        if not GEOJSON_PATH.exists():
            uploaded_geojson = st.file_uploader(
                "Upload GeoJSON batas wilayah",
                type=["geojson", "json"],
                help="File akan digunakan sebagai sumber batas wilayah untuk sesi aplikasi ini.",
            )

with st.spinner("Memuat data EWS dan batas wilayah Jawa Timur..."):
    try:
        df = load_dashboard(uploaded_csv)
    except Exception as exc:
        st.error(f"Gagal membaca dataset EWS: {exc}")
        st.stop()

    try:
        geojson_data = load_geojson(uploaded_geojson)
    except Exception as exc:
        st.error(f"Gagal membaca GeoJSON: {exc}")
        st.stop()

if df is None:
    st.title("EWS Ketahanan Pangan Jawa Timur")
    st.error(
        "Dataset belum ditemukan. Letakkan file CSV pada folder `data` "
        "atau upload melalui sidebar."
    )
    st.code(
        "data/EWS_Dashboard_Gabungan_2018_2025Q1.csv\n"
        "data/Batas_Kabupaten_Kota_Jawa_Timur.geojson",
        language="text",
    )
    st.stop()

# Filter tahun dan bulan. Pilihan "Semua bulan" mengagregasikan seluruh
# bulan yang tersedia pada tahun tersebut.
years = sorted(df["Tahun"].dropna().unique().astype(int).tolist())
if not years:
    st.error("Tidak ada tahun yang valid dalam dataset.")
    st.stop()

forecast_df = df.loc[df["Tipe_Data"].str.upper() == "FORECAST"].copy()
forecast_years = sorted(forecast_df["Tahun"].dropna().astype(int).unique().tolist())
default_year = forecast_years[-1] if forecast_years else years[-1]

selected_year = st.sidebar.selectbox(
    "Pilih Tahun",
    options=years,
    index=years.index(default_year),
)

year_source = df.loc[df["Tahun"] == selected_year].copy()
months = sorted(year_source["Bulan"].dropna().astype(int).unique().tolist())
if not months:
    st.error("Tidak ada bulan pada tahun yang dipilih.")
    st.stop()

forecast_months_for_year = sorted(
    forecast_df.loc[forecast_df["Tahun"] == selected_year, "Bulan"]
    .dropna().astype(int).unique().tolist()
)
default_month = forecast_months_for_year[0] if forecast_months_for_year else months[0]
month_options = ["Semua bulan"] + months

selected_month = st.sidebar.selectbox(
    "Pilih Bulan",
    options=month_options,
    format_func=lambda m: "Semua Bulan (Agregat Tahunan)" if m == "Semua bulan"
    else MONTH_NAMES.get(int(m), str(m)),
    index=month_options.index(default_month),
    help="Pilih satu bulan untuk melihat kondisi bulanan, atau Semua Bulan untuk melihat akumulasi periode yang tersedia dalam tahun tersebut.",
)

region_options = ["(Semua)"] + sorted(df["Kabupaten_Kota"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox(
    "Pilih Kabupaten/Kota",
    options=region_options,
    index=0,
    help="Pilih (Semua) untuk melihat agregat Provinsi Jawa Timur.",
)



# ============================================================
# MENYIAPKAN DATA PERIODE BULANAN ATAU AGREGAT MULTI-BULAN
# ============================================================

all_months_mode = selected_month == "Semua bulan"
months_in_year = sorted(year_source["Bulan"].dropna().astype(int).unique().tolist())
monthly_coverage = year_source.groupby("Bulan")["Wilayah_Key"].nunique()
full_year = (
    len(months_in_year) == 12
    and set(months_in_year) == set(range(1, 13))
    and len(monthly_coverage) == 12
    and (monthly_coverage == 38).all()
)

if all_months_mode:
    period_source = year_source.copy()
    period = aggregate_by_region(period_source)
    if months_in_year:
        month_labels = [MONTH_NAMES[m] for m in months_in_year]
        if months_in_year == list(range(months_in_year[0], months_in_year[-1] + 1)):
            period_month_label = (
                month_labels[0] if len(month_labels) == 1
                else f"{month_labels[0]}–{month_labels[-1]}"
            )
        else:
            period_month_label = ", ".join(month_labels)
    else:
        period_month_label = "Periode tersedia"
    period_label = f"{period_month_label} {selected_year}"
    if not full_year:
        period_label += f" ({len(months_in_year)}/12 bulan tersedia)"
else:
    period_source = year_source.loc[year_source["Bulan"] == int(selected_month)].copy()
    period = period_source.copy()
    period_label = f"{MONTH_NAMES[int(selected_month)]} {selected_year}"

period = period.sort_values("FSR", ascending=True, na_position="last")
if period.empty:
    st.warning("Tidak ada data untuk periode yang dipilih.")
    st.stop()

if period["Wilayah_Key"].duplicated().any():
    st.error("Dataset memiliki duplikasi wilayah pada periode terpilih.")
    st.stop()

n_regions = period["Wilayah_Key"].nunique()
if n_regions != 38:
    st.warning(
        f"Periode ini memuat {n_regions} wilayah, bukan 38. "
        "Periksa kelengkapan data sebelum interpretasi."
    )

period_type = (
    "FORECAST"
    if (period_source["Tipe_Data"].str.upper() == "FORECAST").any()
    else "HISTORIS"
)

# Detail agregat provinsi atau kabupaten/kota mengikuti filter periode.
if selected_region == "(Semua)":
    agg_detail = aggregate_period(period)
    focus_region = "Agregat Jawa Timur"
    focus_row = {
        "Kabupaten_Kota": focus_region,
        "Produksi_Padi_Ton_GKG": agg_detail["gkg"],
        "Food_Availability_Ton": agg_detail["fa"],
        "Food_Requirement_Ton_Bulan": agg_detail["fr"],
        "FSR": agg_detail["fsr"],
        "Status_Ketahanan_Pangan": agg_detail["status"],
        "Probabilitas_Defisit_Persen": np.nan,
    }
else:
    focus_region = selected_region
    selected_rows = period.loc[period["Kabupaten_Kota"] == focus_region]
    if selected_rows.empty:
        st.error(f"Tidak ada data untuk {focus_region} pada periode terpilih.")
        st.stop()
    focus_row = selected_rows.iloc[0]


# ============================================================
# HEADER DAN KPI
# ============================================================

subtitle_type = "Forecast" if period_type == "FORECAST" else "Historis"
st.markdown(
    f"""
    <div class="hero-header">
        <div class="hero-main">
            {"<img class='hero-seal' src='" + LOGO_JATIM_URI + "' alt='Logo Jawa Timur'>" if LOGO_JATIM_URI else ""}
            <div>
                <div class="hero-kicker">Sistem Pemantauan Ketahanan Pangan · Jawa Timur</div>
                <div class="main-title">EWS Ketahanan Pangan Jawa Timur</div>
                <div class="main-subtitle">Berdasarkan produksi padi · {period_label} · {subtitle_type}</div>
            </div>
        </div>
        <div class="hero-logos">
            {"<div class='logo-chip'><img src='" + LOGO_BPS_URI + "' alt='BPS Jawa Timur'></div>" if LOGO_BPS_URI else ""}
            {"<div class='logo-chip'><img src='" + LOGO_TELKOM_URI + "' alt='Telkom University'></div>" if LOGO_TELKOM_URI else ""}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

counts = period["Status_Ketahanan_Pangan"].value_counts()
caption_kpi = "Kabupaten/Kota · periode tersedia" if all_months_mode and not full_year else "Kabupaten/Kota"
c1, c2, c3 = st.columns(3)
with c1:
    metric_card("Aman", int(counts.get("Aman", 0)), STATUS_COLORS["Aman"], caption_kpi)
with c2:
    metric_card("Waspada", int(counts.get("Waspada", 0)), "#D69E00", caption_kpi)
with c3:
    metric_card("Kritis", int(counts.get("Kritis", 0)), STATUS_COLORS["Kritis"], caption_kpi)

if all_months_mode and not full_year:
    st.info(
        f"Agregasi mencakup {len(months_in_year)} dari 12 bulan yang tersedia pada "
        f"{selected_year}. FSR dan surplus/defisit di bawah merupakan akumulasi "
        "periode tersedia, bukan kondisi satu tahun penuh."
    )

st.write("")


# ============================================================
# PETA FULL WIDTH, KEMUDIAN GRAFIK PRODUKSI
# ============================================================

map_title = "Peta Status FSR Kabupaten/Kota Jawa Timur"
st.markdown(f'<div class="panel-title">{map_title}</div>', unsafe_allow_html=True)
if all_months_mode:
    st.caption(f"Warna peta menunjukkan klasifikasi FSR akumulasi periode tersedia: {period_label}.")
if geojson_data is None:
    st.warning(
        "GeoJSON belum ditemukan. Letakkan file batas wilayah pada folder "
        "`data` atau upload melalui sidebar."
    )
else:
    map_obj, matched_count = build_map(period, geojson_data)
    if map_obj is None:
        st.error("Tidak ada fitur GeoJSON yang cocok dengan data EWS.")
    else:
        if matched_count != 38:
            st.warning(f"Peta mencocokkan {matched_count} dari 38 wilayah.")
        with st.spinner("Menyiapkan peta dan memvisualisasikan status ketahanan pangan Jawa Timur..."):
            st_folium(
                map_obj,
                width=1250,
                height=590,
                returned_objects=[],
                key=f"map_full_{selected_year}_{'ALL' if all_months_mode else selected_month}",
            )

st.markdown("---")

if selected_region == "(Semua)":
    chart_title = "Produksi Padi — Agregat Jawa Timur"
    chart_source = year_source.copy()
    chart_grouped = (
        chart_source.groupby("Bulan", as_index=False)
        .agg(Produksi_Padi_Ton_GKG=("Produksi_Padi_Ton_GKG", "sum"))
        .sort_values("Bulan")
    )
else:
    chart_title = f"Produksi Padi — {selected_region}"
    chart_grouped = (
        year_source.loc[
            year_source["Kabupaten_Kota"] == selected_region,
            ["Bulan", "Produksi_Padi_Ton_GKG"],
        ].groupby("Bulan", as_index=False)
        .agg(Produksi_Padi_Ton_GKG=("Produksi_Padi_Ton_GKG", "sum"))
        .sort_values("Bulan")
    )

chart_kind = "Forecast" if period_type == "FORECAST" else "Historis"
chart_title = f"{chart_kind} {chart_title}"
st.markdown(f'<div class="panel-title">{chart_title}</div>', unsafe_allow_html=True)
fig = go.Figure()
if not chart_grouped.empty:
    fig.add_trace(
        go.Scatter(
            x=[MONTH_SHORT.get(int(m), str(m)) for m in chart_grouped["Bulan"]],
            y=chart_grouped["Produksi_Padi_Ton_GKG"],
            mode="lines+markers",
            line=dict(color="#55D69A", width=3.2),
            marker=dict(size=8, color="#E0BD63", line=dict(color="#F6F2DA", width=1.2)),
            name="Produksi padi",
            hovertemplate="%{x}<br>%{y:,.2f} ton GKG<extra></extra>",
        )
    )
fig.update_layout(
    height=390,
    margin=dict(l=10, r=18, t=18, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Bulan",
    yaxis_title="Produksi padi (ton GKG)",
    font=dict(color="#E5F0E7", size=12),
    showlegend=False,
)
fig.update_yaxes(gridcolor="rgba(220,240,222,0.13)", zeroline=False, tickfont=dict(color="#C6D9CB"), title_font=dict(color="#D8E8DB"))
fig.update_xaxes(showgrid=False, tickfont=dict(color="#C6D9CB"), title_font=dict(color="#D8E8DB"))
st.plotly_chart(fig, use_container_width=True)


# ============================================================
# DETAIL WILAYAH DAN KETERANGAN STATUS
# ============================================================

st.markdown("---")
detail_col, legend_col = st.columns([1.8, 1])

if all_months_mode:
    production_label = f"Produksi padi ({period_label})"
    availability_label = f"Ketersediaan beras ({period_label})"
    requirement_label = f"Kebutuhan beras ({period_label})"
    fsr_label = "FSR periode tersedia" if not full_year else "FSR tahunan"
    status_label = "Status periode tersedia" if not full_year else "Status tahunan"
    # Keterangan cakupan periode sudah ditampilkan pada Periode analisis
    # dan informasi kelengkapan data; badge cukup menampilkan statusnya.
    status_text = str(focus_row["Status_Ketahanan_Pangan"])
else:
    production_label = f"Produksi padi ({period_label})"
    availability_label = f"Ketersediaan beras ({period_label})"
    requirement_label = f"Kebutuhan beras ({period_label})"
    fsr_label = f"FSR ({period_label})"
    status_label = "Status Ketahanan Pangan"
    status_text = str(focus_row["Status_Ketahanan_Pangan"])

with detail_col:
    status = str(focus_row["Status_Ketahanan_Pangan"])
    status_color = STATUS_COLORS.get(status, "#667085")
    prob = focus_row.get("Probabilitas_Defisit_Persen")
    if all_months_mode:
        prob_text = "Tidak dihitung untuk agregasi multi-bulan"
    elif pd.notna(prob):
        prob_text = f"{fmt_number(prob, 2)}%"
    elif selected_region == "(Semua)" and period_type == "FORECAST":
        prob_text = "Tidak dihitung untuk agregat"
    else:
        prob_text = "Tidak tersedia untuk data historis"

    saldo = (
        focus_row.get("Food_Availability_Ton", np.nan)
        - focus_row.get("Food_Requirement_Ton_Bulan", np.nan)
    )
    saldo_label = "Surplus" if pd.notna(saldo) and saldo > 0 else "Defisit" if pd.notna(saldo) and saldo < 0 else "Seimbang"
    detail_title = "Detail Agregat Provinsi" if selected_region == "(Semua)" else "Detail Kabupaten/Kota"

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">{detail_title}</div>
            <div class="detail-row"><span>Periode analisis</span><span>:</span>
                <span class="detail-value">{period_label}</span></div>
            <div class="detail-row"><span>Kabupaten/Kota</span><span>:</span>
                <span class="detail-value">{focus_region}</span></div>
            <div class="detail-row"><span>{production_label}</span><span>:</span>
                <span class="detail-value">{fmt_ton(focus_row.get("Produksi_Padi_Ton_GKG"), 2)} GKG</span></div>
            <div class="detail-row"><span>{availability_label}</span><span>:</span>
                <span class="detail-value">{fmt_ton(focus_row.get("Food_Availability_Ton"), 2)}</span></div>
            <div class="detail-row"><span>{requirement_label}</span><span>:</span>
                <span class="detail-value">{fmt_ton(focus_row.get("Food_Requirement_Ton_Bulan"), 2)}</span></div>
            <div class="detail-row"><span>Saldo pangan</span><span>:</span>
                <span class="detail-value">{saldo_label} {fmt_ton(abs(saldo), 2)}</span></div>
            <div class="detail-row"><span>{fsr_label}</span><span>:</span>
                <span class="detail-value">{fmt_number(focus_row.get("FSR"), 3)}</span></div>
            <div class="detail-row"><span>{status_label}</span><span>:</span>
                <span class="status-pill" style="background:{status_color};color:#ffffff">{status_text.upper()}</span></div>
            <div class="detail-row"><span>Probabilitas Defisit Pangan</span><span>:</span>
                <span class="detail-value" style="color:{status_color}">{prob_text}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with legend_col:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Keterangan Status</div>
            <div class="detail-row"><span style="color:#35A66F">■ Aman</span>
                <span> </span><span>FSR ≥ 1,20</span></div>
            <div class="detail-row"><span style="color:#B8860B">■ Waspada</span>
                <span> </span><span>1,00 ≤ FSR &lt; 1,20</span></div>
            <div class="detail-row"><span style="color:#E94B4B">■ Kritis</span>
                <span> </span><span>FSR &lt; 1,00</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TABEL RINGKASAN
# ============================================================

st.markdown('<div class="panel-title">Tabel Ringkasan Kabupaten/Kota</div>', unsafe_allow_html=True)

table = period.copy()
table["No"] = range(1, len(table) + 1)
if all_months_mode:
    fsr_column = "FSR (Periode Tersedia)" if not full_year else "FSR (Tahunan)"
    status_column = "Status Periode Tersedia" if not full_year else "Status Tahunan"
    table = table[
        [
            "No", "Kabupaten_Kota", "Produksi_Padi_Ton_GKG",
            "Food_Availability_Ton", "Food_Requirement_Ton_Bulan", "FSR",
            "Status_Ketahanan_Pangan",
        ]
    ].rename(
        columns={
            "Kabupaten_Kota": "Kabupaten/Kota",
            "Produksi_Padi_Ton_GKG": "Produksi Padi (Ton GKG)",
            "Food_Availability_Ton": "Ketersediaan Beras (Ton)",
            "Food_Requirement_Ton_Bulan": "Kebutuhan Beras (Ton)",
            "FSR": fsr_column,
            "Status_Ketahanan_Pangan": status_column,
        }
    )
else:
    fsr_column = f"FSR ({period_label})"
    table = table[
        [
            "No", "Kabupaten_Kota", "Produksi_Padi_Ton_GKG",
            "FSR", "Probabilitas_Defisit_Persen",
            "Status_Ketahanan_Pangan",
        ]
    ].rename(
        columns={
            "Kabupaten_Kota": "Kabupaten/Kota",
            "Produksi_Padi_Ton_GKG": "Produksi Padi (Ton GKG)",
            "FSR": fsr_column,
            "Probabilitas_Defisit_Persen": "Prob. Defisit (%)",
            "Status_Ketahanan_Pangan": "Status",
        }
    )

if selected_region != "(Semua)":
    table = table.loc[table["Kabupaten/Kota"] == selected_region]

number_config = {
    "Produksi Padi (Ton GKG)": st.column_config.NumberColumn(format="%.2f"),
    fsr_column: st.column_config.NumberColumn(format="%.3f"),
}
if all_months_mode:
    number_config["Ketersediaan Beras (Ton)"] = st.column_config.NumberColumn(format="%.2f")
    number_config["Kebutuhan Beras (Ton)"] = st.column_config.NumberColumn(format="%.2f")
else:
    number_config["Prob. Defisit (%)"] = st.column_config.NumberColumn(format="%.2f")

# Warna tabel dibuat hijau pastel agar selaras dengan latar dashboard,
# tetapi tetap menjaga kontras teks dan keterbacaan angka.
def pastel_row_style(row):
    row_bg = "#F7FBF8" if row.name % 2 == 0 else "#EAF4ED"
    return [
        f"background-color: {row_bg}; color: #244634; border-color: #D5E5D9;"
        for _ in row
    ]


def pastel_status_style(value):
    value = str(value).strip().lower()
    if value == "aman":
        return (
            "background-color: #D9F0E1; color: #246344; "
            "font-weight: 700; border-color: #C2DEC9;"
        )
    if value == "waspada":
        return (
            "background-color: #FFF2CC; color: #795B12; "
            "font-weight: 700; border-color: #EAD99D;"
        )
    if value == "kritis":
        return (
            "background-color: #FBE1DE; color: #963D36; "
            "font-weight: 700; border-color: #EBC4BF;"
        )
    return "background-color: #EEF4EF; color: #365747;"


styled_table = (
    table.style
    .set_table_styles([
        {
            "selector": "th",
            "props": [
                ("background-color", "#DDEFE3"),
                ("color", "#194D35"),
                ("font-weight", "700"),
                ("border", "1px solid #C9DDCF"),
                ("padding", "9px 10px"),
            ],
        },
        {
            "selector": "td",
            "props": [
                ("border", "1px solid #D7E6DB"),
                ("padding", "8px 10px"),
            ],
        },
        {
            "selector": "table",
            "props": [
                ("border-collapse", "collapse"),
                ("border-radius", "10px"),
                ("overflow", "hidden"),
            ],
        },
    ])
    .apply(pastel_row_style, axis=1)
)

for status_col in [col for col in table.columns if "status" in col.lower()]:
    styled_table = styled_table.map(pastel_status_style, subset=[status_col])

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True,
    column_config=number_config,
)

st.markdown("---")
st.caption(
    "Catatan metodologis: ketersediaan pangan dihitung dari produksi beras lokal "
    "(produksi padi × faktor rendemen 0,6274). Hasil ini belum memperhitungkan "
    "stok, arus distribusi antardaerah, atau pasokan dari luar wilayah. "
    "Forecast pada dataset saat ini bersifat bersyarat pada jalur variabel eksogen (EO)."
)
st.markdown("<div style=\"text-align:center;color:#a9c2b1;font-size:.72rem;letter-spacing:.5px;padding:8px 0 2px;\">EWS KETAHANAN PANGAN JAWA TIMUR · SISTEM PEMANTAUAN DAN PERINGATAN DINI</div>", unsafe_allow_html=True)
