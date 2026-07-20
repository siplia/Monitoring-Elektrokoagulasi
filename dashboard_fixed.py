import streamlit as st
import time
import base64
import gspread

from google.oauth2.service_account import Credentials

# CONFIG
st.set_page_config(
    page_title="Monitoring Air IoT",
    layout="wide"
)

# ==========================
# GOOGLE SHEETS
# ==========================
# Cara 1 (lokal): butuh file "service_account.json" di folder yang sama.
# Cara 2 (Streamlit Cloud): isi kredensial lewat menu Secrets di app
# settings, dengan key "gcp_service_account" (format TOML, lihat panduan).
# Kode ini otomatis pakai Secrets kalau ada, kalau nggak ada baru pakai
# file lokal -- jadi bisa dipakai di laptop maupun di Streamlit Cloud
# tanpa ubah kode.

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_ID = "1XBRrdHekddN7OKxU0ZZPZZ-VcndZnLGQsdirHEhhSwg"

@st.cache_resource
def get_sheet():
    import os
    if os.path.exists("service_account.json"):
        creds = Credentials.from_service_account_file(
            "service_account.json",
            scopes=scope
        )
    else:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=scope
        )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


def get_latest_data(tempat):
    try:
        sheet = get_sheet()
        data = sheet.get_all_records()
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheet: {e}")
        return None

    data_tempat = [d for d in data if d.get("Tempat") == tempat]

    if not data_tempat:
        return None

    return data_tempat[-1]


# ==========================
# KLASIFIKASI (disamakan dgn firmware)
# ==========================

def status_ph(ph):
    ph = float(ph)
    if 6.5 <= ph <= 8.5:
        return "Memenuhi Standar WHO"
    elif ph < 6.5:
        return "Di Bawah Standar WHO"
    else:
        return "Di Atas Standar WHO"


def status_tds(ppm):
    ppm = float(ppm)
    if ppm <= 300:
        return "Ideal"
    elif ppm <= 600:
        return "Acceptable"
    elif ppm <= 900:
        return "Borderline"
    elif ppm <= 1200:
        return "High Minerals"
    elif ppm <= 1500:
        return "Possibly Hazard"
    else:
        return "Hazard"


def status_turbidity(ntu):
    ntu = float(ntu)
    if ntu <= 1.5:
        return "Sangat Jernih"
    elif ntu <= 5:
        return "Memenuhi Standar WHO"
    elif ntu <= 25:
        return "Agak Keruh"
    elif ntu <= 100:
        return "Keruh"
    elif ntu <= 500:
        return "Sangat Keruh"
    else:
        return "Ekstrem"


def status_ec(ec):
    ec = float(ec)
    if ec <= 400:
        return "Sangat Baik"
    elif ec <= 800:
        return "Baik"
    elif ec <= 1200:
        return "Cukup"
    else:
        return "Buruk"

# ===== FUNGSI BASE64 =====
def get_image_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

# ===== FUNGSI HEADER =====
def show_header():
    logo_b64 = get_image_base64("logo_unj.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:100px;height:100px;border-radius:50%;object-fit:cover;border:3px solid rgba(255,255,255,0.6);">' if logo_b64 else ""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #A4C6EB, #BBD7F0);
        padding: 25px 45px;
        border-radius: 24px;
        box-shadow: 0 6px 22px rgba(164,198,235,0.3);
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div>
            <div class="header-title">💧 Water Quality Monitoring</div>
            <div class="header-subtitle">Smart Monitoring System</div>
        </div>
        {logo_html}
    </div>
    """, unsafe_allow_html=True)

# ===== CSS =====
st.markdown("""
<style>

.block-container {
    padding-top: 3rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

.stApp {
    background-color: #F0F6FF;
}

div[data-testid="stAlert"] p {
    color: #1a3a5c !important;
}
h1, h2, h3, h4, h5, h6 {
    color: #1a3a5c !important;
}
[data-testid="stMarkdownContainer"] p {
    color: #1a3a5c !important;
}

[data-testid="stSidebar"]{
    background-color: #BBD7F0;
    width: 200px !important;
    min-width: 200px !important;
}

[data-testid="stSidebar"] * {
    color: #1a3a5c !important;
}

.header-title{
    font-size: 38px;
    font-weight: 800;
    color: #1a3a5c;
    margin-bottom: 8px;
}

.header-subtitle{
    color: #2c5f8a;
    font-size: 16px;
}

.card {
    background-color: white;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0px 4px 12px rgba(164,198,235,0.25);
    text-align: center;
    margin-bottom: 15px;
    border-top: 5px solid #A4C6EB;
}

.title {
    font-size: 18px;
    font-weight: bold;
    color: #1a3a5c;
}

.value {
    font-size: 24px;
    color: #2c5f8a;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ===== LOGIN SYSTEM =====
if "login" not in st.session_state:
    st.session_state.login = False

# ===== LOGIN PAGE =====
if not st.session_state.login:

    st.markdown("""
    <style>

    .stApp{
        background: linear-gradient(135deg, #C5D9DF, #BBD7F0);
    }

    header{ visibility:hidden; }

    [data-testid="stSidebar"]{ display:none; }

    .login-container{
        background: rgba(255,255,255,0.45);
        border: 1px solid rgba(255,255,255,0.6);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        padding: 45px;
        border-radius: 28px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(164,198,235,0.3);
        margin-bottom: 10px;
    }

    .logo{
        font-size: 75px;
        margin-bottom: 10px;
        filter: drop-shadow(0px 4px 10px rgba(0,0,0,0.1));
    }

    .title-login{
        font-size: 44px;
        font-weight: 800;
        color: #1a3a5c;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }

    .subtitle{
        color: #2c5f8a;
        font-size: 17px;
        letter-spacing: 0.5px;
    }

    div[data-baseweb="input"]{
        background: rgba(255,255,255,0.85) !important;
        border-radius: 14px !important;
        border: none !important;
    }

    div[data-baseweb="input"] input {
        background: rgba(255,255,255,0.85) !important;
        color: #1a3a5c !important;
        font-size: 16px !important;
    }

    div[data-baseweb="base-input"] {
        background: rgba(255,255,255,0.85) !important;
        border-radius: 14px !important;
    }

    input{
        color: #1a3a5c !important;
        font-size: 16px !important;
    }

    input::placeholder{
        color: #7aafd4 !important;
    }

    button[data-testid="passwordInputVisibilityToggle"] {
        color: #1a3a5c !important;
        background: transparent !important;
    }
    button[data-testid="passwordInputVisibilityToggle"] svg {
        fill: #1a3a5c !important;
        stroke: #1a3a5c !important;
        color: #1a3a5c !important;
        opacity: 1 !important;
    }
    [data-baseweb="input"] svg {
        fill: #1a3a5c !important;
        stroke: #1a3a5c !important;
        opacity: 1 !important;
    }

    .stButton{
        display: flex;
        justify-content: center;
    }

    .stButton > button{
        width: 100%;
        height: 52px;
        border: none;
        border-radius: 14px;
        background: #A4C6EB !important;
        color: #1a3a5c !important;
        font-size: 18px;
        font-weight: bold;
        transition: 0.3s;
        box-shadow: 0 4px 18px rgba(164,198,235,0.4);
    }

    .stButton > button:hover{
        transform: translateY(-2px);
        background: #7aafd4 !important;
        color: white !important;
    }

    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        st.markdown("""
        <div class="login-container">
            <div class="logo">💧</div>
            <div class="title-login">Water Quality</div>
            <div class="subtitle">Smart Monitoring System</div>
        </div>
        """, unsafe_allow_html=True)

        st.info('Demo access — Username: **matcha**  |  Password: **latte**')

        username = st.text_input("", placeholder="👤 Username")
        password = st.text_input("", type="password", placeholder="🔒 Password")

        if st.button("LOGIN"):
            if username == "matcha" and password == "latte":
                st.success("Login berhasil!")
                time.sleep(1)
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Username atau password salah")

    st.stop()




# ===== SIDEBAR =====
st.sidebar.title("🌊 Monitoring Air")

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "📍 Tempat 1",
        "📍 Tempat 2",
        "📍 Tempat 3",
        "📍 Tempat 4",
        "📍 Tempat 5",
        "📊 Monitoring",
        "📝 Data Record",
        "ℹ️ About"
    ]
)

# ===== DATA SISTEM =====
data_sistem = {
    "Jenis Plat": "Alumunium",
    "Frekuensi": "500 Hz",
    "Duty Cycle": "25%",
    "Jumlah Plat": "4"
}

# ===== DASHBOARD =====
if menu == "🏠 Dashboard":

    show_header()

    st.subheader("⚙️ Data Sistem")

    keys = list(data_sistem.keys())

    for row_start in range(0, len(keys), 3):
        row_keys = keys[row_start:row_start + 3]
        cols = st.columns(3)
        for i, key in enumerate(row_keys):
            with cols[i]:
                st.markdown(f"""
                <div class="card">
                    <div class="title">{key}</div>
                    <div class="value">{data_sistem[key]}</div>
                </div>
                """, unsafe_allow_html=True)

# ===== HALAMAN TEMPAT =====
elif "📍 Tempat" in menu:

    tempat = menu.replace("📍 ", "")
    latest = get_latest_data(tempat)

    show_header()
    st.title(f"📍 Monitoring {tempat}")

    if latest is None:
        st.warning("Belum ada data untuk lokasi ini.")
        st.stop()

    waktu = latest.get("Waktu", "-")

    ph_before = latest.get("pH Sebelum", 0)
    ph_after = latest.get("pH Sesudah", 0)

    tds_before = latest.get("TDS Sebelum", 0)
    tds_after = latest.get("TDS Sesudah", 0)

    tur_before = latest.get("Turbidity Sebelum", 0)
    tur_after = latest.get("Turbidity Sesudah", 0)

    ec_before = latest.get("EC Sebelum", 0)
    ec_after = latest.get("EC Sesudah", 0)

    st.markdown(f"""
    <div class="card">
        <h3>⏰ Informasi Waktu</h3>
        <p><b>Waktu Pengukuran:</b> {waktu}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 Parameter Air")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>💧 pH</h3>
            <div class="value">{ph_before} → {ph_after}</div>
            <p>{status_ph(ph_before)} → {status_ph(ph_after)}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <h3>📊 TDS</h3>
            <div class="value">{tds_before} → {tds_after}</div>
            <p>{status_tds(tds_before)} → {status_tds(tds_after)}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <h3>🌫 Turbidity</h3>
            <div class="value">{tur_before} → {tur_after}</div>
            <p>{status_turbidity(tur_before)} → {status_turbidity(tur_after)}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="card">
            <h3>⚡ EC (estimasi)</h3>
            <div class="value">{ec_before} → {ec_after}</div>
            <p>{status_ec(ec_before)} → {status_ec(ec_after)}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h2 style="color:#2c7a2c;">
        ✅ Hasil Proses : BERHASIL
        </h2>
    </div>
    """, unsafe_allow_html=True)

# ===== MONITORING =====
elif menu == "📊 Monitoring":

    show_header()
    st.title("📊 Monitoring")
    st.info("Halaman monitoring akan ditambahkan di sini.")

# ===== DATA RECORD =====
elif menu == "📝 Data Record":

    show_header()
    st.title("📝 Data Record")
    st.info("Halaman data record akan ditambahkan di sini.")

# ===== ABOUT =====
elif menu == "ℹ️ About":

    show_header()
    st.title("ℹ️ About")
    st.info("Halaman about akan ditambahkan di sini.")
