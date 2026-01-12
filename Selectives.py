import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Payment Summary | Rose Edition", layout="wide", page_icon="🌹")

# --- CUSTOM CSS: FORCING LIGHT ROSE THEME ---
st.markdown("""
    <style>
    /* Force Light Mode Background and Text Colors */
    .stApp {
        background-color: #FFF5F7 !important;
        color: #4B0082 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFB6C1 !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #8B008B !important;
        font-weight: bold !important;
    }

    /* Header Title */
    h1 {
        color: #D02090 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
    }

    /* Dataframe Visibility */
    [data-testid="stDataFrame"] {
        background-color: white !important;
        border: 2px solid #FF69B4;
        border-radius: 10px;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #FF69B4 !important;
        color: white !important;
        border-radius: 12px !important;
        border: 2px solid #FF1493 !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 6])
with col1:
    # High-quality Rose icon for the UI
    st.image("https://img.icons8.com/emoji/96/rose.png", width=80)
with col2:
    st.title("Rose Payment Summary Tool")
    st.markdown("<p style='color: #FF69B4;'>Professional data processing with a Rose aesthetic. ✨</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🌹 Upload Data")
monitoring_file = st.sidebar.file_uploader("Upload Monitoring XLSX", type=['xlsx'])
selectives_file = st.sidebar.file_uploader("Upload Selectives XLSX", type=['xlsx'])

def deep_clean_id(series):
    """Cleans IDs to ensure they are plain strings without decimals."""
    cleaned = pd.to_numeric(series, errors='coerce')
    return cleaned.fillna(0).astype(np.int64).astype(str).str.strip()

def to_excel_pro(df):
    """Generates the Rose-styled Excel file matching your requirements."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary')
        
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        
        # 1. Hide Gridlines
        worksheet.hide_gridlines(2)

        # 2. Define Formats
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
            'fg_color': '#FF69B4', 'font_color': 'white', 'border': 1
        })
        
        # PN Number Format (Text only, no decimals/commas)
        pn_format = workbook.add_format({'align': 'left', 'border': 1, 'num_format': '@'})
        
        # Standard Data Format (Borders only)
        data_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        
        # Currency Format
        num_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        # 3. Apply Styling and Auto-Fit
        for col_num, value in enumerate(df.columns.values):
            # Write Header
            worksheet.write(0, col_num, value, header_format)
            
            # Set Column Width and Formats
            max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2
            
            if value == "PN NUMBERS":
                worksheet.set_column(col_num, col_num, max_len, pn_format)
            elif "AMOUNT" in value.upper():
                worksheet.set_column(col_num, col_num, max_len, num_format)
            else:
                worksheet.set_column(col_num, col_num, max_len, data_format)

    return output.getvalue()

if monitoring_file and selectives_file:
    try:
        df_mon = pd.read_excel(monitoring_file, engine='openpyxl')
        df_sel = pd.read_excel(selectives_file, engine='openpyxl')

        # Processing logic
        df_mon.columns = df_mon.columns.str.strip()
        df_sel.columns = df_sel.columns.str.strip()

        df_mon['PN_CLEAN'] = deep_clean_id(df_mon['PN NUMBERS'])
        df_sel['SEL_CLEAN'] = deep_clean_id(df_sel['RECON_DEAL_REF'])

        df_sel_grouped = df_sel.groupby('SEL_CLEAN').agg({
            'PAYMENT': 'sum',
            'TRANSACTION_DATE': 'max'
        }).reset_index()

        df_mon_unique = df_mon.groupby('PN_CLEAN').agg({
            'PN NUMBERS': 'first',
            'CLIENT NAME': 'first',
            'PTP AMOUNT': 'sum'
        }).reset_index()

        summary_df = pd.merge(df_mon_unique, df_sel_grouped, left_on='PN_CLEAN', right_on='SEL_CLEAN', how='left')
        
        # Formatting for display
        summary_df['Selective Amount'] = summary_df['PAYMENT'].fillna(0)
        summary_df['Transaction Date'] = summary_df['TRANSACTION_DATE'].dt.strftime('%Y-%m-%d').fillna("No Transaction")
        
        # Convert PN Numbers back to strings to prevent UI decimals
        summary_df['PN NUMBERS'] = summary_df['PN NUMBERS'].astype(np.int64).astype(str)

        final_table = summary_df[['PN NUMBERS', 'CLIENT NAME', 'PTP AMOUNT', 'Selective Amount', 'Transaction Date']]

        # --- UI DISPLAY ---
        st.success(f"🌹 Processed {len(final_table)} records successfully.")
        st.dataframe(final_table, use_container_width=True)

        # --- DOWNLOAD ---
        excel_data = to_excel_pro(final_table)
        st.sidebar.markdown("---")
        st.sidebar.download_button(
            label="🎀 Download Rose XLSX Report",
            data=excel_data,
            file_name="Rose_Payment_Summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.info("Please upload both files to start the Rose magic! 🌹")
