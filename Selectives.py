import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Payment Summary | Pink Edition", layout="wide", page_icon="🌸")

# --- CUSTOM CSS: FORCING LIGHT THEME & DARK MODE OVERRIDE ---
st.markdown("""
    <style>
    /* Force Light Mode Background for the entire app */
    .stApp {
        background-color: #FFF5F7 !important;
        color: #4B0082 !important;
    }

    /* Force Sidebar to stay Pink */
    section[data-testid="stSidebar"] {
        background-color: #FFB6C1 !important;
    }

    /* Override Dark Mode Text in Sidebar */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #8B008B !important;
        font-weight: bold !important;
    }

    /* Main Header Styling */
    h1 {
        color: #D02090 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        text-shadow: 1px 1px 2px #FFB6C1;
    }

    /* Professional Table Container - Force White Background */
    [data-testid="stTable"], [data-testid="stDataFrame"] {
        background-color: white !important;
        padding: 10px;
        border-radius: 10px;
        border: 2px solid #FF69B4;
    }

    /* Info/Success Boxes */
    .stAlert {
        background-color: #FFE4E1 !important;
        color: #D02090 !important;
        border: 1px solid #FF69B4 !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #FF69B4 !important;
        color: white !important;
        border-radius: 12px !important;
        border: 2px solid #FF1493 !important;
        padding: 0.5rem 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER SECTION ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://img.icons8.com/illustrations/official/256/anime-girl.png", width=100)
with col2:
    st.title("Payment Monitoring Summary Tool")
    st.markdown("<p style='color: #FF69B4;'>✨ Generating professional reports with precision.</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🌸 Upload Data")
monitoring_file = st.sidebar.file_uploader("1. Monitoring XLSX", type=['xlsx'])
selectives_file = st.sidebar.file_uploader("2. Selectives XLSX", type=['xlsx'])

def deep_clean_id(series):
    cleaned = pd.to_numeric(series, errors='coerce')
    return cleaned.fillna(0).astype(np.int64).astype(str).str.strip()

def to_excel_pro(df):
    """Generates a professional Excel file with auto-fit, no gridlines, and styling."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary Report')
        
        workbook = writer.book
        worksheet = writer.sheets['Summary Report']
        
        # 1. Remove Gridlines
        worksheet.hide_gridlines(2) 

        # 2. Define Formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#FF69B4',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'num_format': '#,##0.00'
        })

        # 3. Apply Header Format and Auto-Fit Columns
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
            # Auto-fit logic: find max length of column content
            column_len = df[value].astype(str).str.len().max()
            column_len = max(column_len, len(value)) + 2 # Add padding
            worksheet.set_column(col_num, col_num, column_len)

        # 4. Add a subtle border to the whole data range
        worksheet.set_column(0, len(df.columns) - 1, None, cell_format)

    return output.getvalue()

if monitoring_file and selectives_file:
    try:
        df_mon = pd.read_excel(monitoring_file, engine='openpyxl')
        df_sel = pd.read_excel(selectives_file, engine='openpyxl')

        # Clean Columns
        df_mon.columns = df_mon.columns.str.strip()
        df_sel.columns = df_sel.columns.str.strip()

        # ID Cleaning
        df_mon['PN_CLEAN'] = deep_clean_id(df_mon['PN NUMBERS'])
        df_sel['SEL_CLEAN'] = deep_clean_id(df_sel['RECON_DEAL_REF'])

        # Numeric and Date cleaning
        df_sel['PAYMENT'] = pd.to_numeric(df_sel['PAYMENT'], errors='coerce').fillna(0)
        df_mon['PTP AMOUNT'] = pd.to_numeric(df_mon['PTP AMOUNT'], errors='coerce').fillna(0)
        df_sel['TRANSACTION_DATE'] = pd.to_datetime(df_sel['TRANSACTION_DATE'], errors='coerce')

        # Aggregate Selectives (Sum payments)
        df_sel_grouped = df_sel.groupby('SEL_CLEAN').agg({
            'PAYMENT': 'sum',
            'TRANSACTION_DATE': 'max'
        }).reset_index()

        # Aggregate Monitoring (Unique rows)
        df_mon_unique = df_mon.groupby('PN_CLEAN').agg({
            'PN NUMBERS': 'first',
            'CLIENT NAME': 'first',
            'PTP AMOUNT': 'sum'
        }).reset_index()

        # Merge
        summary_df = pd.merge(df_mon_unique, df_sel_grouped, left_on='PN_CLEAN', right_on='SEL_CLEAN', how='left')
        
        summary_df['PAYMENT'] = summary_df['PAYMENT'].fillna(0)
        summary_df['Date'] = summary_df['TRANSACTION_DATE'].dt.strftime('%Y-%m-%d').fillna("No Transaction")

        final_table = summary_df.rename(columns={
            'PAYMENT': 'Selective Amount',
            'Date': 'Transaction Date'
        })[['PN NUMBERS', 'CLIENT NAME', 'PTP AMOUNT', 'Selective Amount', 'Transaction Date']]

        # --- DISPLAY ---
        st.success(f"💖 Processed {len(final_table)} unique clients successfully.")
        
        # Use container width for auto-fit UI feel
        st.dataframe(final_table, use_container_width=True)

        # --- DOWNLOAD ---
        excel_data = to_excel_pro(final_table)
        st.sidebar.markdown("---")
        st.sidebar.download_button(
            label="🎀 Download Pro XLSX Report",
            data=excel_data,
            file_name="Payment_Summary_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error, senpai! Please check your file columns. Error: {e}")
else:
    st.info("Waiting for your files to start the magic! ✨")
