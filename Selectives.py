import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Payment Monitoring Summary", layout="wide")

st.title("📊 Payment Monitoring Summary Tool")

# --- SIDEBAR: FILE UPLOADER ---
st.sidebar.header("Upload Data Files")

monitoring_file = st.sidebar.file_uploader("1. Upload Monitoring XLSX", type=['xlsx'])
selectives_file = st.sidebar.file_uploader("2. Upload Selectives XLSX", type=['xlsx'])

def deep_clean_id(series):
    """
    Ensures long PN Numbers match by removing decimals, 
    scientific notation, and hidden spaces.
    """
    # Convert to numeric first to handle scientific notation
    cleaned = pd.to_numeric(series, errors='coerce')
    # Use int64 to keep large numbers whole, then string for matching
    return cleaned.fillna(0).astype(np.int64).astype(str).str.strip()

if monitoring_file and selectives_file:
    try:
        # Load Data
        df_mon = pd.read_excel(monitoring_file)
        df_sel = pd.read_excel(selectives_file)

        # 1. Clean Column Headers
        df_mon.columns = df_mon.columns.str.strip()
        df_sel.columns = df_sel.columns.str.strip()

        # 2. APPLY DEEP CLEAN to ID columns for matching
        df_mon['PN_CLEAN'] = deep_clean_id(df_mon['PN NUMBERS'])
        df_sel['SEL_CLEAN'] = deep_clean_id(df_sel['RECON_DEAL_REF'])

        # 3. Clean Date and Payment types
        df_sel['TRANSACTION_DATE'] = pd.to_datetime(df_sel['TRANSACTION_DATE'], errors='coerce')
        df_sel['PAYMENT'] = pd.to_numeric(df_sel['PAYMENT'], errors='coerce').fillna(0)
        df_mon['PTP AMOUNT'] = pd.to_numeric(df_mon['PTP AMOUNT'], errors='coerce').fillna(0)

        # --- PROCESSING: AGGREGATION ---
        
        # Step A: Group Selectives (Sum payments and get latest date)
        df_sel_grouped = df_sel.groupby('SEL_CLEAN').agg({
            'PAYMENT': 'sum',
            'TRANSACTION_DATE': 'max'
        }).reset_index()

        # Step B: Group Monitoring (To make PN Numbers unique and sum PTP if duplicates exist)
        df_mon_unique = df_mon.groupby('PN_CLEAN').agg({
            'PN NUMBERS': 'first',
            'CLIENT NAME': 'first',
            'PTP AMOUNT': 'sum'
        }).reset_index()

        # Step C: Merge unique records
        summary_df = pd.merge(
            df_mon_unique, 
            df_sel_grouped, 
            left_on='PN_CLEAN', 
            right_on='SEL_CLEAN', 
            how='left'
        )

        # 4. Final Formatting
        summary_df['PAYMENT'] = summary_df['PAYMENT'].fillna(0)
        summary_df['TRANSACTION_DATE_STR'] = summary_df['TRANSACTION_DATE'].dt.strftime('%Y-%m-%d').fillna("No Transaction")

        # Select and Rename for display
        final_table = summary_df.rename(columns={
            'PAYMENT': 'Selective Amount',
            'TRANSACTION_DATE_STR': 'Transaction Date'
        })[['PN NUMBERS', 'CLIENT NAME', 'PTP AMOUNT', 'Selective Amount', 'Transaction Date']]

        # --- DISPLAY ---
        st.subheader("Summary Table")
        
        # Metric calculation
        total_matched = (final_table['Selective Amount'] > 0).sum()
        st.info(f"💡 Found payments for **{total_matched}** out of **{len(final_table)}** unique clients.")
        
        # Display the unique table
        st.dataframe(final_table, use_container_width=True)

        # Download Button
        csv = final_table.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="💾 Download Unique Summary (CSV)",
            data=csv,
            file_name="Unique_Payment_Summary.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Error processing files: {e}")
        st.warning("Please ensure your column names match: 'PN NUMBERS', 'PTP AMOUNT' in file 1 and 'RECON_DEAL_REF', 'PAYMENT', 'TRANSACTION_DATE' in file 2.")
else:
    st.info("Please upload both Excel files to generate the unique summary report.")