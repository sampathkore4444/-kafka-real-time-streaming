import streamlit as st
import pandas as pd
import oracledb
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# Streamlit auto-refresh
# -----------------------------
st_autorefresh(interval=15000, key="refresh")  # 15 sec refresh

# -----------------------------
# Oracle DB connection
# -----------------------------
ORACLE_USER = "SYSTEM"
ORACLE_PASSWORD = "LOMA@1234"
ORACLE_DSN = "localhost/XE"


@st.cache_resource
def get_connection():
    return oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)


conn = get_connection()


# -----------------------------
# Utility functions
# -----------------------------
@st.cache_data(ttl=15)
def fetch_kpis():
    query = """
        SELECT
            SUM(total_amount) AS total_gmv,
            SUM(txn_count) AS total_txns,
            COUNT(DISTINCT merchant_id) AS active_merchants
        FROM merchant_agg
        WHERE window_start >= TRUNC(SYSDATE)
    """
    return pd.read_sql(query, conn)


@st.cache_data(ttl=15)
def fetch_ranking(top_n=10):
    query = f"""
        SELECT
            merchant_id,
            SUM(total_amount) AS gmv,
            SUM(txn_count) AS txns
        FROM merchant_agg
        WHERE window_start >= TRUNC(SYSDATE)
        GROUP BY merchant_id
        ORDER BY gmv DESC
        FETCH FIRST {top_n} ROWS ONLY
    """
    return pd.read_sql(query, conn)


@st.cache_data(ttl=15)
def fetch_late_events():
    query = """
        SELECT COUNT(*) AS late_count
        FROM merchant_agg
        WHERE is_late = 'Y'
          AND window_start >= TRUNC(SYSDATE)
    """
    df = pd.read_sql(query, conn)
    return int(df["LATE_COUNT"].iloc[0])


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Merchant Dashboard", layout="wide")
st.title("🏦 Merchant Dashboard (Real-Time)")

# 1️⃣ KPIs
kpi_df = fetch_kpis()
col1, col2, col3 = st.columns(3)
col1.metric("Total GMV Today", f"${kpi_df['TOTAL_GMV'].iloc[0]:,.2f}")
col2.metric("Total Transactions Today", int(kpi_df["TOTAL_TXNS"].iloc[0]))
col3.metric("Active Merchants", int(kpi_df["ACTIVE_MERCHANTS"].iloc[0]))

# 2️⃣ Late Event Badge
late_count = fetch_late_events()
if late_count > 0:
    st.warning(f"⚠ {late_count} late-event corrections applied today")
else:
    st.success("✅ All data finalized")

# 3️⃣ Merchant Ranking
st.subheader("Top Merchants by GMV Today")
ranking_df = fetch_ranking()
st.dataframe(ranking_df)

# 4️⃣ GMV Trend Chart (last 24h)
st.subheader("GMV Trend (Last 24h)")
trend_query = """
    SELECT
        TRUNC(window_start, 'HH24') AS hour_slot,
        SUM(total_amount) AS gmv
    FROM merchant_agg
    WHERE window_start >= SYSDATE - 1
    GROUP BY TRUNC(window_start, 'HH24')
    ORDER BY hour_slot
"""
trend_df = pd.read_sql(trend_query, conn)
st.line_chart(trend_df.rename(columns={"HOUR_SLOT": "index"}).set_index("index")["GMV"])

# 5️⃣ Optional Filters
st.sidebar.subheader("Filters")
selected_merchant = st.sidebar.selectbox(
    "Select Merchant", ["All"] + ranking_df["MERCHANT_ID"].tolist()
)

if selected_merchant != "All":
    merchant_query = f"""
        SELECT
            TRUNC(window_start) AS business_date,
            SUM(total_amount) AS gmv,
            SUM(txn_count) AS txns
        FROM merchant_agg
        WHERE merchant_id = '{selected_merchant}'
        GROUP BY TRUNC(window_start)
        ORDER BY business_date
    """
    merchant_df = pd.read_sql(merchant_query, conn)
    st.subheader(f"Daily GMV & Transactions for {selected_merchant}")
    st.bar_chart(
        merchant_df.rename(columns={"BUSINESS_DATE": "index"}).set_index("index")[
            ["GMV", "TXNS"]
        ]
    )

st.caption("🔄 Dashboard auto-refreshes every 15 seconds")
