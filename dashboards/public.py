import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import Client

def app(supabase: Client):
    st.set_page_config(
        page_title="Loanalyze - Public Dashboard",
        layout="wide"
    )

    st.title("Loanalyze — Public Dashboard")

    st.markdown("""
Welcome to **Loanalyze Public Dashboard** — a transparent view of all loan activities and predictions.

We display:
- Total users & roles
- Banks’ uploads & clients processed
- Risk band breakdown
- Average loan amounts
- Application & upload trends
    """)

    try:
        with st.spinner("Loading all public dashboard data..."):
            applicants = supabase.table("applicant_submissions").select("*").execute().data
            users = supabase.table("user_profile").select("*").execute().data
            uploads = supabase.table("bank_uploads").select("*").execute().data
            bank_clients = supabase.table("bank_clients").select("*").execute().data

            df_applicants = pd.DataFrame(applicants)
            df_users = pd.DataFrame(users)
            df_uploads = pd.DataFrame(uploads)
            df_clients = pd.DataFrame(bank_clients)

        ### 1️⃣ User Stats
        st.subheader("Platform Users Overview")
        total_users = len(df_users)
        role_breakdown = df_users["role"].value_counts().reset_index()
        role_breakdown.columns = ["Role", "Count"]

        col1, col2 = st.columns(2)
        col1.metric("Total Registered Users", f"{total_users:,}")
        col2.dataframe(role_breakdown, use_container_width=True)

        st.markdown("---")

        ### 2️⃣ Applicants: Risk Bands & Loans
        st.subheader("Applicants — Risk Bands & Loans")
        if not df_applicants.empty:
            if "created_at" in df_applicants.columns:
                df_applicants["created_at"] = pd.to_datetime(df_applicants["created_at"])

            if "risk_band" in df_applicants.columns:
                risk_counts = df_applicants["risk_band"].value_counts().reset_index()
                risk_counts.columns = ["Risk Band", "Count"]
                pie_fig = px.pie(
                    risk_counts, names="Risk Band", values="Count",
                    title="Applicant Submissions — Risk Bands",
                    color="Risk Band",
                    color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"}
                )
                st.plotly_chart(pie_fig, use_container_width=True)

            if "loan_amount" in df_applicants.columns:
                avg_loan = df_applicants["loan_amount"].mean()
                st.metric("Average Requested Loan", f"₹ {avg_loan:,.2f}")

            if "created_at" in df_applicants.columns:
                trend = df_applicants.groupby(df_applicants["created_at"].dt.date).size().reset_index(name="Applications")
                trend.columns = ["Date", "Applications"]
                line_fig = px.line(trend, x="Date", y="Applications", markers=True, title="Applications Over Time")
                st.plotly_chart(line_fig, use_container_width=True)

        else:
            st.info("No applicant submissions yet.")

        st.markdown("---")

        ### 3️⃣ Banks: Uploads & Clients
        st.subheader("Banks — Uploads & Clients Processed")

        total_uploads = len(df_uploads)
        total_clients = len(df_clients)

        col1, col2 = st.columns(2)
        col1.metric("Total Bank Uploads", f"{total_uploads:,}")
        col2.metric("Total Clients Processed", f"{total_clients:,}")

        if not df_uploads.empty and "created_at" in df_uploads.columns:
            df_uploads["created_at"] = pd.to_datetime(df_uploads["created_at"])
            trend_uploads = df_uploads.groupby(df_uploads["created_at"].dt.date).size().reset_index(name="Uploads")
            trend_uploads.columns = ["Date", "Uploads"]
            upload_fig = px.line(trend_uploads, x="Date", y="Uploads", markers=True, title="Bank Uploads Over Time")
            st.plotly_chart(upload_fig, use_container_width=True)

        if not df_clients.empty and "risk_band" in df_clients.columns:
            risk_client_counts = df_clients["risk_band"].value_counts().reset_index()
            risk_client_counts.columns = ["Risk Band", "Count"]
            bar_fig = px.bar(risk_client_counts, x="Risk Band", y="Count",
                             color="Risk Band",
                             color_discrete_map={"Low": "green", "Medium": "orange", "High": "red"},
                             title="Bank Clients — Risk Band Breakdown")
            st.plotly_chart(bar_fig, use_container_width=True)

        st.success("Dashboard covers all live data!")

    except Exception as e:
        st.error(f"Failed to load dashboard: {e}")

    if st.button("Return to Home"):
        st.session_state.page = "Home"
        st.rerun()
