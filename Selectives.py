import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Payment Summary | Pink Edition", layout="wide", page_icon="🌸")

# --- CUSTOM CSS FOR ANIME PINK THEME ---
st.markdown("""
    <style>
    /* Main Background and Text */
    .stApp {
        background-color: #FFF0F5;
    }
    
    /* Header Styling */
    h1 {
        color: #D02090;
        font-family: 'Comic Sans MS', cursive, sans-serif;
        text-shadow: 2px 2px #FFB6C1;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFB6C1 !important;
    }
    
    section[data-testid="stSidebar"] .stText, section[data-testid="stSidebar"] label {
        color: #8B008B !important;
        font-weight: bold;
    }

    /* Professional Table Container */
    .stDataFrame {
        border: 2px solid #FF69B4;
        border-radius: 10px;
        background-color: white;
    }

    /* Info Box */
    .stAlert {
        background-color: #FFD1DC;
        border: 1px solid #FF69B4;
        color: #D02090;
    }

    /* Buttons */
    .stButton>button {
        background-color: #FF69B4;
        color: white;
        border-radius: 20px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #D02090;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- UI HEADER WITH ANIME AESTHETIC ---
col1, col2 = st.columns([1, 4])
with col1:
    # Using a high-quality placeholder for a pink anime girl avatar
    st.image("https://img.icons8.com/illustrations/official/256/anime-girl.png", width=120)
with col2:
    st.title("Payment Monitoring Summary")
    st.caption("Professional Results with a Touch of Kawaii ✨")

# --- SIDEBAR ---
st.sidebar.header("🌸 Upload Data")
monitoring_file = st.sidebar.file_uploader("1. Monitoring XLSX", type=['xlsx'])
selectives_file = st.sidebar.file_uploader("2. Selectives XLSX", type=['xlsx'])

def deep_clean_id(series):
    cleaned = pd.to_numeric(series, errors='coerce')
    return cleaned.fillna(0).astype(np.int64).astype(str).str.strip()

def to_excel(df):
    """Converts dataframe to a professional Excel file in memory."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary')
        # Professional formatting
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'fg_color': '#FF69B4', 'font_color': 'white', 'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    return output.getvalue()

if monitoring_file and selectives_file:
    try:
        df_mon = pd.read_excel(monitoring_file, engine='openpyxl')
        df_sel = pd.read_excel(selectives_file, engine='openpyxl')

        df_mon.columns = df_mon.columns.str.strip()
        df_sel.columns = df_sel.columns.str.strip()

        # Processing
        df_mon['PN_CLEAN'] = deep_clean_id(df_mon['PN NUMBERS'])
        df_sel['SEL_CLEAN'] = deep_clean_id(df_sel['RECON_DEAL_REF'])

        df_sel['PAYMENT'] = pd.to_numeric(df_sel['PAYMENT'], errors='coerce').fillna(0)
        df_sel['TRANSACTION_DATE'] = pd.to_datetime(df_sel['TRANSACTION_DATE'], errors='coerce')

        # Aggregate Selectives
        df_sel_grouped = df_sel.groupby('SEL_CLEAN').agg({
            'PAYMENT': 'sum',
            'TRANSACTION_DATE': 'max'
        }).reset_index()

        # Aggregate Monitoring (Unique Result)
        df_mon_unique = df_mon.groupby('PN_CLEAN').agg({
            'PN NUMBERS': 'first',
            'CLIENT NAME': 'first',
            'PTP AMOUNT': 'sum'
        }).reset_index()

        # Merge
        summary_df = pd.merge(df_mon_unique, df_sel_grouped, left_on='PN_CLEAN', right_on='SEL_CLEAN', how='left')
        
        # Cleanup
        summary_df['PAYMENT'] = summary_df['PAYMENT'].fillna(0)
        summary_df['Date'] = summary_df['TRANSACTION_DATE'].dt.strftime('%Y-%m-%d').fillna("No Transaction")

        final_table = summary_df.rename(columns={
            'PAYMENT': 'Selective Amount',
            'Date': 'Transaction Date'
        })[['PN NUMBERS', 'CLIENT NAME', 'PTP AMOUNT', 'Selective Amount', 'Transaction Date']]

        # --- DISPLAY ---
        st.info(f"💖 Processed {len(final_table)} unique client records successfully.")
        st.dataframe(final_table, use_container_width=True)

        # Download as XLSX
        excel_data = to_excel(final_table)
        st.sidebar.markdown("---")
        st.sidebar.download_button(
            label="🎀 Download XLSX Summary",
            data=excel_data,
            file_name="Professional_Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Something went wrong, senpai! Error: {e}")
else:
    st.warning("Please upload both Excel files to start the magic! ✨")
