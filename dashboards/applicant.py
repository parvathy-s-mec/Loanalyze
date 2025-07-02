import streamlit as st
import numpy as np
import pickle
import os
from supabase import Client
from dotenv import load_dotenv
import pandas as pd
from fpdf import FPDF
import tempfile
from io import BytesIO

def app(supabase: Client):
    st.set_page_config(page_title="Applicant Dashboard", layout="centered")

    if "user" not in st.session_state:
        st.warning("Please log in to continue.")
        st.stop()

    user = st.session_state["user"]

    if user.get("role") != "applicant":
        st.error("This page is only for applicants.")
        st.stop()

    st.title(f"Applicant Dashboard — Welcome, {user.get('full_name', 'User')}")
    st.write("Fill in your loan application details:")

    # Load model and encoders
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(BASE_DIR, "model", "loan_model.pkl"), "rb") as f:
        model = pickle.load(f)

    with open(os.path.join(BASE_DIR, "model", "label_encoders.pkl"), "rb") as f:
        label_encoders = pickle.load(f)

    # Fetch class options
    marital_status = st.selectbox("Marital Status", label_encoders["marital_status"].classes_)
    house_ownership = st.selectbox("House Ownership", label_encoders["House_Ownership"].classes_)
    car_ownership = st.selectbox("Car Ownership", label_encoders["Car_Ownership"].classes_)
    profession = st.selectbox("Profession", label_encoders["Profession"].classes_)
    city = st.selectbox("City", label_encoders["CITY"].classes_)
    state = st.selectbox("State", label_encoders["STATE"].classes_)

    income = st.number_input("Monthly Income", min_value=1000)
    age = st.number_input("Age", min_value=18)
    experience = st.number_input("Work Experience (years)", min_value=0)
    job_years = st.number_input("Years in Current Job", min_value=0)
    house_years = st.number_input("Years at Current Residence", min_value=0)
    loan_amount = st.number_input("Requested Loan Amount", min_value=1000)
    loan_duration = st.slider("Loan Duration (months)", min_value=12, max_value=360, step=12)
    interest_rate = st.slider("Interest Rate (%)", min_value=5.0, max_value=20.0, step=0.1)

    # Optional comment field for the applicant
    comments = st.text_area("Additional Comments (optional)")

    if st.button("Predict & Submit"):
        try:
            # Encode values
            marital_status_enc = label_encoders["marital_status"].transform([marital_status])[0]
            house_ownership_enc = label_encoders["House_Ownership"].transform([house_ownership])[0]
            car_ownership_enc = label_encoders["Car_Ownership"].transform([car_ownership])[0]
            profession_enc = label_encoders["Profession"].transform([profession])[0]
            city_enc = label_encoders["CITY"].transform([city])[0]
            state_enc = label_encoders["STATE"].transform([state])[0]

            input_data = np.array([[income, age, experience, marital_status_enc,
                                    house_ownership_enc, car_ownership_enc, profession_enc,
                                    city_enc, state_enc, job_years, house_years]])

            prediction = model.predict(input_data)[0]
            default_prob = round(model.predict_proba(input_data)[0][1], 2)

            if default_prob < 0.3:
                risk_band = "Low"
            elif default_prob < 0.7:
                risk_band = "Medium"
            else:
                risk_band = "High"

            estimated_profit = loan_amount * (interest_rate / 100) * (1 - default_prob)

            st.success(f"Predicted Default Probability: {default_prob * 100:.2f}%")
            st.info(f"Risk Band: {risk_band}")

            # Add optional feature importance placeholder if you wish
            feature_importance = {}

            insert_data = {
                "user_id": user["user_id"],
                "income": income,
                "age": age,
                "experience": experience,
                "marital_status": marital_status,
                "house_ownership": house_ownership,
                "car_ownership": car_ownership,
                "profession": profession,
                "city": city,
                "state": state,
                "job_years": job_years,
                "house_years": house_years,
                "loan_amount": loan_amount,
                "prediction": int(prediction),
                "default_probability": float(default_prob),
                "risk_band": risk_band,
                "loan_duration": loan_duration,
                "interest_rate": float(interest_rate),
                "estimated_profit": float(estimated_profit),
                "prediction_status": "success",
                "comments": comments.strip() if comments else None,
                "feature_importance": feature_importance
            }

            response = supabase.table("applicant_submissions").insert(insert_data).execute()

            if hasattr(response, "error") and response.error:
                st.error(f"Failed to save submission: {response.error.message}")
            else:
                st.success("Submission saved successfully!")

                # Generate PDF summary
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Loan Application Summary", ln=True, align='C')
                pdf.ln(10)

                for k, v in insert_data.items():
                    pdf.cell(200, 10, txt=f"{k.replace('_', ' ').title()}: {v}", ln=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    tmp_file.seek(0)
                    pdf_bytes = tmp_file.read()
                    st.download_button("Download PDF Summary", data=pdf_bytes, file_name="loan_summary.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Prediction failed: {e}")

    # Submission History
    st.markdown("---")
    st.subheader("Submission History")
    try:
        history = supabase.table("applicant_submissions").select("*").eq("user_id", user["user_id"]).execute()
        if hasattr(history, "data") and history.data:
            df = pd.DataFrame(history.data)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇ Download History as CSV", data=csv, file_name="submission_history.csv")
        else:
            st.info("No submissions found yet.")
    except Exception as e:
        st.error(f"Error fetching history: {e}")

    if st.button("Log Out"):
        st.session_state.clear()
        st.session_state.page = "Home"
        st.rerun()
