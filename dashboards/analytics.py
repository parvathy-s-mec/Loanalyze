import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import Client
from typing import Callable
import os
from dotenv import load_dotenv

# --------------------
# ANALYTICS DASHBOARD MODULE
# --------------------
def app(supabase: Client):
    st.set_page_config(page_title="Loan Analytics", layout="wide")
    st.title("Loan Data Analytics")

    try:
        response = supabase.table("applicant_submissions").select("*").execute()

        if response.error:
            st.error(f"❌ Failed to fetch submissions: {response.error.message}")
            return

        data = response.data
        if not data:
            st.info("No applicant submissions available.")
            return

        df = pd.DataFrame(data)

        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])

        st.subheader("Loan Amount Distribution")
        fig1 = px.histogram(df, x="loan_amount", nbins=20, title="Loan Amount Histogram")
        st.plotly_chart(fig1, use_container_width=True)

        if "loan_purpose" in df.columns:
            st.subheader("Default Risk by Loan Purpose")
            fig2 = px.box(df, x="loan_purpose", y="loan_amount", color="prediction", 
                         title="Loan Amount by Purpose & Default")
            st.plotly_chart(fig2, use_container_width=True)

        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        if numeric_cols:
            st.subheader("Correlation Heatmap")
            corr_matrix = df[numeric_cols].corr().round(2)
            st.dataframe(corr_matrix)

    except Exception as e:
        st.error(f"Error loading analytics: {e}")

    if st.button("Log Out"):
        st.session_state.clear()
        st.session_state.page = "Home"
        st.rerun()
