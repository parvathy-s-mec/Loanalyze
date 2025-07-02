import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import Client


def app(supabase: Client):
    st.set_page_config(page_title="Admin Dashboard", layout="wide")
    st.title("Admin Dashboard")

    # --------------------------------
    # Auth check
    # --------------------------------
    if "user" not in st.session_state:
        st.warning("Please log in as admin.")
        st.stop()

    user = st.session_state["user"]
    if user.get("role") != "admin":
        st.error("Access denied. Admins only.")
        st.stop()

    st.success(f"Welcome, {user.get('full_name', 'Admin')}")

    try:
        # ==============================
        # 👥 Registered Users
        # ==============================
        st.subheader("👥 Registered Users")
        users_resp = supabase.table("user_profile").select("*").execute()
        users_df = pd.DataFrame(users_resp.data)

        if users_df.empty:
            st.info("No registered users found.")
        else:
            role_filter = st.selectbox("Filter by Role", ["All"] + sorted(users_df["role"].dropna().unique()))
            if role_filter != "All":
                users_df = users_df[users_df["role"] == role_filter]

            st.dataframe(users_df, use_container_width=True)
            st.download_button(
                label="⬇ Download Users CSV",
                data=users_df.to_csv(index=False),
                file_name="registered_users.csv"
            )

        # ==============================
        # 📄 Applicant Submissions
        # ==============================
        st.subheader("📄 Applicant Submissions")
        subs_resp = supabase.table("applicant_submissions").select("*").execute()
        subs_df = pd.DataFrame(subs_resp.data)

        if subs_df.empty:
            st.info("No applicant submissions yet.")
        else:
            st.dataframe(subs_df, use_container_width=True)
            st.download_button(
                label="⬇ Download Submissions CSV",
                data=subs_df.to_csv(index=False),
                file_name="applicant_submissions.csv"
            )

            st.markdown("###Submissions Stats")
            st.metric("Total Submissions", len(subs_df))
            st.metric("Average Loan Amount", f"₹ {subs_df['loan_amount'].mean():,.2f}")
            st.metric("Low Risk Count", sum(subs_df['risk_band'] == 'Low'))
            st.metric("Medium Risk Count", sum(subs_df['risk_band'] == 'Medium'))
            st.metric("High Risk Count", sum(subs_df['risk_band'] == 'High'))

        # ==============================
        # 🏦 Bank Uploads
        # ==============================
        st.subheader("Bank Uploads")
        uploads_resp = supabase.table("bank_uploads").select("*").execute()
        uploads_df = pd.DataFrame(uploads_resp.data)

        if uploads_df.empty:
            st.info("No bank uploads yet.")
        else:
            st.dataframe(uploads_df, use_container_width=True)
            st.download_button(
                label="⬇ Download Bank Uploads CSV",
                data=uploads_df.to_csv(index=False),
                file_name="bank_uploads.csv"
            )

        # ==============================
        # 📜 Audit Logs
        # ==============================
        st.subheader("Audit Logs")
        logs_resp = supabase.table("audit_logs").select("*").execute()
        logs_df = pd.DataFrame(logs_resp.data)

        if logs_df.empty:
            st.info("No audit logs found.")
        else:
            # Merge user names if possible
            if not users_df.empty:
                logs_df = logs_df.merge(
                    users_df[["user_id", "full_name"]],
                    left_on="user_id",
                    right_on="user_id",
                    how="left"
                )

            # Filters
            actions = logs_df['action'].dropna().unique().tolist()
            selected_actions = st.multiselect("Filter by Action", actions, default=actions)

            statuses = logs_df['status'].dropna().unique().tolist()
            selected_statuses = st.multiselect("Filter by Status", statuses, default=statuses)

            logs_df['created_at'] = pd.to_datetime(logs_df['created_at'])
            min_date = logs_df['created_at'].min().date()
            max_date = logs_df['created_at'].max().date()
            date_range = st.date_input("Date Range", [min_date, max_date])

            filtered_logs = logs_df[
                logs_df['action'].isin(selected_actions) &
                logs_df['status'].isin(selected_statuses) &
                (logs_df['created_at'].dt.date >= date_range[0]) &
                (logs_df['created_at'].dt.date <= date_range[1])
            ]

            st.dataframe(filtered_logs, use_container_width=True)

            # Trend chart
            trend = filtered_logs.groupby(
                [filtered_logs['created_at'].dt.date, 'action']
            ).size().reset_index(name="Count")
            trend.columns = ["Date", "Action", "Count"]

            if not trend.empty:
                fig = px.bar(
                    trend,
                    x="Date",
                    y="Count",
                    color="Action",
                    barmode="group",
                    title="Audit Actions Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                label="⬇ Download Logs CSV",
                data=filtered_logs.to_csv(index=False),
                file_name="audit_logs.csv"
            )

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

    if st.button("Log Out"):
        st.session_state.clear()
        st.session_state.page = "Home"
        st.rerun()
