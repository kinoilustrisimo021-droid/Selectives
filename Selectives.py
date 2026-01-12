import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rose Payment Summary", layout="wide", page_icon="🌹")

# --- FORCED LIGHT ROSE THEME (DARK MODE PROOF) ---
st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7 !important; color: #4B0082 !important; }
    [data-testid="stSidebar"] { background-color: #FFB6C1 !important; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #8B008B !important; font-weight: bold !important;
    }
    h1 { color: #D02090 !important; font-family: 'Segoe UI', sans-serif; font-weight: 800; }
    [data-testid="stDataFrame"] { background-color: white !important; border: 2px solid #FF69B4; border-radius: 10px; }
    .stButton>button {
        background-color: #FF69B4 !important; color: white !important;
        border-radius: 12px !important; border: 2px solid #FF1493 !important; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🌹 Rose Payment Summary Tool")
st.sidebar.header("🌹 Upload Data")
monitoring_file = st.sidebar.file_uploader("Upload Monitoring XLSX", type=['xlsx'])
selectives_file = st.sidebar.file_uploader("Upload Selectives XLSX", type=['xlsx'])

def deep_clean_id(series):
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(np.int64).astype(str).str.strip()

def to_excel_pro(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary')
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        worksheet.hide_gridlines(2)

        # FORMATS
        header_fmt = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
            'fg_color': '#FF69B4', 'font_color': 'white', 'border': 1
        })
        
        # Data format with border
        border_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        # Currency format with border
        num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'valign': 'vcenter'})
        # Plain text for PN Numbers
        pn_fmt = workbook.add_format({'border': 1, 'align': 'left', 'num_format': '@'})

        # Apply Header and Auto-fit
        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_fmt)
            
            # Manual Data Writing to avoid "Auto-Borders" on empty rows
            for row_num, value in enumerate(df[col_name]):
                # Only apply border format if there is a row of data
                current_fmt = border_fmt
                if col_name == "PN NUMBERS": current_fmt = pn_fmt
                elif "AMOUNT" in col_name.upper(): current_fmt = num_fmt
                
                worksheet.write(row_num + 1, col_num, value, current_fmt)

            # Auto-fit columns
            max_len = max(df[col_name].astype(str).map(len).max(), len(col_name)) + 2
            worksheet.set_column(col_num, col_num, max_len)

    return output.getvalue()

if monitoring_file and selectives_file:
    try:
        df_mon = pd.read_excel(monitoring_file, engine='openpyxl')
        df_sel = pd.read_excel(selectives_file, engine='openpyxl')

        # CLEANING
        df_mon.columns = df_mon.columns.str.strip()
        df_sel.columns = df_sel.columns.str.strip()
        df_mon['PN_CLEAN'] = deep_clean_id(df_mon['PN NUMBERS'])
        df_sel['SEL_CLEAN'] = deep_clean_id(df_sel['RECON_DEAL_REF'])
        df_sel['PAYMENT'] = pd.to_numeric(df_sel['PAYMENT'], errors='coerce').fillna(0)
        df_mon['PTP AMOUNT'] = pd.to_numeric(df_mon['PTP AMOUNT'], errors='coerce').fillna(0)
        
        # DATE FIX
        df_sel['TRANSACTION_DATE'] = pd.to_datetime(df_sel['TRANSACTION_DATE'], errors='coerce')

        # AGGREGATE
        df_sel_grouped = df_sel.groupby('SEL_CLEAN').agg({'PAYMENT': 'sum', 'TRANSACTION_DATE': 'max'}).reset_index()
        df_mon_unique = df_mon.groupby('PN_CLEAN').agg({'PN NUMBERS': 'first', 'CLIENT NAME': 'first', 'PTP AMOUNT': 'sum'}).reset_index()

        # MERGE
        summary_df = pd.merge(df_mon_unique, df_sel_grouped, left_on='PN_CLEAN', right_on='SEL_CLEAN', how='left')
        summary_df['Selective Amount'] = summary_df['PAYMENT'].fillna(0)
        summary_df['Transaction Date'] = summary_df['TRANSACTION_DATE'].dt.strftime('%Y-%m-%d').fillna("No Transaction")
        summary_df['PN NUMBERS'] = summary_df['PN_CLEAN']

        final_table = summary_df[['PN NUMBERS', 'CLIENT NAME', 'PTP AMOUNT', 'Selective Amount', 'Transaction Date']]

        # DISPLAY
        st.success(f"🌹 Processed {len(final_table)} unique records successfully.")
        st.dataframe(final_table, use_container_width=True)

        # DOWNLOAD
        excel_data = to_excel_pro(final_table)
        st.sidebar.download_button(label="🎀 Download Rose XLSX Report", data=excel_data, 
                                   file_name="Rose_Summary.xlsx", mime="application/vnd.ms-excel")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload both files to start! 🌹")
