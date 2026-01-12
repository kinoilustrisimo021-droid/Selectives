import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Payment Summary | Rose Edition", layout="wide", page_icon="🌹")

# --- CSS FOR FORCED ROSE THEME & DARK MODE OVERRIDE ---
st.markdown("""
    <style>
    /* Force Light Rose Background and Dark Purple Text globally */
    .stApp {
        background-color: #FFF5F7 !important;
        color: #4B0082 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #FFB6C1 !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #8B008B !important;
        font-weight: bold !important;
    }

    /* Main Title and Subtitle */
    h1 {
        color: #D02090 !important;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 800;
    }

    /* Ensure Dataframe is always visible in White */
    [data-testid="stDataFrame"] {
        background-color: white !important;
        border: 2px solid #FF69B4;
        border-radius: 10px;
    }

    /* Professional Button */
    .stButton>button {
        background-color: #FF69B4 !important;
        color: white !important;
        border-radius: 12px !important;
        border: 2px solid #FF1493 !important;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://img.icons8.com/emoji/96/rose.png", width=80)
with col2:
    st.title("Rose Payment Summary Tool")
    st.markdown("<p style='color: #FF69B4;'>Professional data processing with a Rose aesthetic. ✨</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🌹 Upload Data")
monitoring_file = st.sidebar.file_uploader("Upload Monitoring XLSX", type=['xlsx'])
selectives_file = st.sidebar.file_uploader("Upload Selectives XLSX", type=['xlsx'])

def deep_clean_id(series):
    """Ensures PN Numbers are cleaned of decimals and notation."""
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(np.int64).astype(str).str.strip()

def to_excel_pro(df):
    """Generates Rose-styled Excel: no commas in IDs, auto-fit, and wrap text."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary')
        
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        worksheet.hide_gridlines(2) # Remove gridlines

        # FORMATS
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
            'fg_color': '#FF69B4', 'font_color': 'white', 'border': 1
        })
        
        # ID format: Plain text, no commas, no decimals
        pn_format = workbook.add_format({'align': 'left', 'border': 1, 'num_format': '@'})
        
        # Standard Data Format
        data_format = workbook.add_format({'border': 1, 'valign': 'vcenter', 'align': 'left'})
        
        # Currency Format
        num_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'valign': 'vcenter'})

        # Apply Header and Auto-fit
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
            # Find max length for auto-fit
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

        df_mon.columns = df_mon.columns.str.strip()
        df_sel.columns = df_sel.columns.str.strip()

        # Step 1: Deep Clean IDs
        df_mon['PN_CLEAN'] = deep_clean_id(df_mon['PN NUMBERS'])
        df_sel['SEL_CLEAN'] = deep_clean_id(df_sel['RECON_DEAL_REF'])

        # Step 2: Clean Currency
        df_sel['PAYMENT'] = pd.to_numeric(df_sel['PAYMENT'], errors='coerce').fillna(0)
        df_mon['PTP AMOUNT'] = pd.to_numeric(df_mon['PTP AMOUNT'], errors='coerce').fillna(0)

        # Step 3: Handle Dates (Fixes the 'agg' error)
        df_sel['TRANSACTION_DATE'] = pd.to_datetime(df_sel['TRANSACTION_DATE'], errors='coerce')

        # Step 4: Aggregate (Unique Rows)
        df_sel_grouped = df_sel.groupby('SEL_CLEAN').agg({
            'PAYMENT': 'sum',
            'TRANSACTION_DATE': 'max' # Now works because it's purely datetime or NaT
        }).reset_index()

        df_mon_unique = df_mon.groupby('PN_CLEAN').agg({
            'PN NUMBERS': 'first',
            'CLIENT NAME': 'first',
            'PTP AMOUNT': 'sum'
        }).reset_index()

        # Step 5: Merge
        summary_df = pd.merge(df_mon_unique, df_sel_grouped, left_on='PN_CLEAN', right_on='SEL_CLEAN', how='left')
        
        # Step 6: Final Table Cleanup
        summary_df['Selective Amount'] = summary_df['PAYMENT'].fillna(0)
        summary_df['Transaction Date'] = summary_df['TRANSACTION_DATE'].dt.strftime('%Y-%m-%d').fillna("No Transaction")
        
        # Ensure PN Numbers display correctly in UI (No decimals)
        summary_df['PN NUMBERS'] = summary_df['PN_CLEAN']

        final_table = summary_df[['PN NUMBERS', 'CLIENT NAME', 'PTP AMOUNT', 'Selective Amount', 'Transaction Date']]

        # --- DISPLAY ---
        st.success(f"🌹 Processed {len(final_table)} unique client records successfully.")
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
    st.info("Please upload both Excel files to start the Rose magic! 🌹")
