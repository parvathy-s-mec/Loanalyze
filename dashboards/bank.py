import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import uuid
from io import BytesIO
from supabase import Client
import matplotlib.pyplot as plt
from fpdf import FPDF


def app(supabase: Client = None):
    st.set_page_config(page_title="Loan Risk Prediction & Bank Dashboard", layout="wide")

    try:
        with open("model/loan_model.pkl", "rb") as f:
            model = pickle.load(f)
        with open("model/label_encoders.pkl", "rb") as f:
            label_encoders = pickle.load(f)
    except Exception as e:
        st.error(f"Failed to load model or encoders: {e}")
        return

    def preprocess_input(df):
        df = df.copy()
        df.rename(columns={
            "Married/Single": "marital_status",
            "CURRENT_JOB_YRS": "job_years",
            "CURRENT_HOUSE_YRS": "house_years"
        }, inplace=True)

        for col in df.select_dtypes(include="object").columns:
            if col in label_encoders:
                le = label_encoders[col]
                df[col] = df[col].map(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            else:
                df[col] = -1
        return df

    def find_column_by_name(possible_names, df_columns):
        return next((col for col in df_columns if col.strip().lower() in [n.lower() for n in possible_names]), None)

    if supabase:
        if "user" not in st.session_state:
            session = supabase.auth.get_session()
            if not session or not session.user:
                st.warning("Please log in to continue.")
                st.stop()

            user_uid = session.user.id

            try:
                res = supabase.table("user_profiles").select("*").eq("user_id", user_uid).single().execute()
                if res.data:
                    st.session_state["user"] = res.data
                else:
                    st.error("User profile not found. Please contact admin.")
                    st.stop()
            except Exception as e:
                st.error(f"Failed to load user profile: {e}")
                st.stop()

        user = st.session_state["user"]
        if user.get("role") != "bank":
            st.error("This page is only for banks.")
            st.stop()

        st.title(f"Bank Dashboard — Welcome, {user.get('full_name', 'User')}")

        try:
            st.subheader("Applicant Submissions")
            response = supabase.table("applicant_submissions").select("*").execute()
            data = response.data
            if not data:
                st.info("No applicant submissions available.")
            else:
                df = pd.DataFrame(data)
                if "created_at" in df.columns:
                    df["created_at"] = pd.to_datetime(df["created_at"])
                    df = df.sort_values(by="created_at", ascending=False)
                st.dataframe(df, use_container_width=True)

                st.subheader("Profit Analysis")
                st.metric("Total Estimated Profit", f"₹ {df.get('estimated_profit', pd.Series(dtype=float)).sum():,.2f}")
                st.metric("Average Default Probability", f"{df.get('default_probability', pd.Series(dtype=float)).mean() * 100:.2f}%")
                st.metric("High Risk Applicants", (df.get("risk_band") == "High").sum())
        except Exception as e:
            st.error(f"Error loading data: {e}")

        st.markdown("---")
        st.subheader("Batch Upload for Prediction")
        uploaded_batch = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"], key="batch")
        notes = st.text_input("Optional Notes about this upload")

        if uploaded_batch:
            try:
                df = pd.read_csv(uploaded_batch) if uploaded_batch.name.endswith(".csv") else pd.read_excel(uploaded_batch)
                st.write("🔍 Preview of uploaded data:")
                st.dataframe(df.head())

                if st.button("🔎 Run Predictions"):
                    df_processed = preprocess_input(df)
                    for col in set(model.feature_names_in_) - set(df_processed.columns):
                        df_processed[col] = 0
                    df_processed = df_processed[model.feature_names_in_]
                    probs = model.predict_proba(df_processed)[:, 1]

                    df["default_probability"] = probs
                    df["risk_band"] = pd.cut(probs, bins=[-1, 0.33, 0.66, 1], labels=["Low", "Medium", "High"])

                    loan_col = find_column_by_name(["Requested Loan Amount", "loan_amount", "Loan_Amount"], df.columns)
                    df["loan_amount"] = pd.to_numeric(df[loan_col], errors="coerce") if loan_col else 0
                    df["loan_amount"] = df["loan_amount"].fillna(0)
                    df["estimated_profit"] = (1 - df["default_probability"]) * df["loan_amount"]

                    st.success("Predictions completed!")
                    st.dataframe(df)

                    upload_id = str(uuid.uuid4())
                    user_id = user.get("user_id")
                    try:
                        supabase.table("bank_uploads").insert({
                            "id": upload_id,
                            "user_id": user_id,
                            "original_filename": uploaded_batch.name,
                            "notes": str(notes),
                            "total_clients": int(len(df)),
                            "low_risk_count": int((df["risk_band"] == "Low").sum()),
                            "medium_risk_count": int((df["risk_band"] == "Medium").sum()),
                            "high_risk_count": int((df["risk_band"] == "High").sum())
                        }).execute()
                    except Exception as e:
                        st.error(f"Upload metadata save failed: {e}")
                        return

                    for i, row in df.iterrows():
                        try:
                            supabase.table("bank_clients").insert({
                                "id": str(uuid.uuid4()),
                                "bank_upload_id": upload_id,
                                "processed_by": user_id,
                                "monthly_income": int(row.get("Monthly Income", 0)),
                                "cibil_score": int(row.get("CIBIL Score", 0)),
                                "requested_loan_amount": int(row.get(loan_col, 0)) if loan_col else 0,
                                "risk_band": row.get("risk_band", None),
                                "feature_importance": {}
                            }).execute()
                        except Exception as e:
                            st.warning(f"Failed to insert row {i}: {e}")

                    st.markdown("### Analytical Visualizations")

                    # Pie Chart
                    fig1, ax1 = plt.subplots(figsize=(5, 5))
                    df["risk_band"].value_counts().plot.pie(
                        autopct="%1.1f%%", startangle=90, ax=ax1, colors=["#28a745", "#ffc107", "#dc3545"]
                    )
                    ax1.set_ylabel("")
                    ax1.set_title("Risk Band Distribution")
                    st.pyplot(fig1)

                    # Bar Chart
                    fig2, ax2 = plt.subplots(figsize=(6, 4))
                    df["risk_band"].value_counts().plot(
                        kind="bar", ax=ax2, color=["#28a745", "#ffc107", "#dc3545"]
                    )
                    ax2.set_title("Applicants per Risk Band")
                    ax2.set_xlabel("Risk Band")
                    ax2.set_ylabel("Count")
                    st.pyplot(fig2)

                    # Histogram
                    fig3, ax3 = plt.subplots(figsize=(6, 4))
                    df["default_probability"].plot(kind="hist", bins=20, ax=ax3, color="#007bff")
                    ax3.set_title("Default Probability Distribution")
                    ax3.set_xlabel("Default Probability")
                    ax3.set_ylabel("Frequency")
                    st.pyplot(fig3)

                    # Loan vs Profit
                    grouped = df.groupby("risk_band")[["loan_amount", "estimated_profit"]].sum()
                    fig4, ax4 = plt.subplots(figsize=(6, 4))
                    grouped.plot(kind="bar", ax=ax4)
                    ax4.set_title("Total Loan Amount & Estimated Profit by Risk Band")
                    ax4.set_xlabel("Risk Band")
                    ax4.set_ylabel("Amount")
                    st.pyplot(fig4)

                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False)

                    st.download_button("Download Prediction Report", excel_buffer.getvalue(), "loan_predictions.xlsx")

                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, "Loan Prediction Report", ln=True, align="C")

                    pdf.set_font("Arial", "", 12)
                    pdf.cell(0, 10, f"Total Applicants: {len(df)}", ln=True)
                    pdf.cell(0, 10, f"Low Risk: {(df['risk_band'] == 'Low').sum()}", ln=True)
                    pdf.cell(0, 10, f"Medium Risk: {(df['risk_band'] == 'Medium').sum()}", ln=True)
                    pdf.cell(0, 10, f"High Risk: {(df['risk_band'] == 'High').sum()}", ln=True)

                    for fig, name in zip(
                        [fig1, fig2, fig3, fig4],
                        ["pie.png", "bar.png", "hist.png", "loan.png"]
                    ):
                        fig.savefig(name, bbox_inches="tight")
                        pdf.add_page()
                        pdf.image(name, x=15, y=30, w=180)

                    pdf_bytes = pdf.output(dest="S").encode("latin1")
                    pdf_buffer = BytesIO(pdf_bytes)
                    st.download_button("Download PDF Report", pdf_buffer, "loan_report.pdf")

            except Exception as e:
                st.error(f"Error processing batch file: {e}")

        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()
