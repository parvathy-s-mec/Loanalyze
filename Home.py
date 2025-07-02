import streamlit as st
import os
from supabase import create_client
from dotenv import load_dotenv

def app(navigate):
    st.set_page_config(page_title="Loanalyze", layout="centered")

    # Initialize session state keys
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None

    # -------------------------------
    # Role selector post-Google login
    # -------------------------------
    if st.session_state.get("user") and st.session_state.get("role") is None:
        st.subheader("Select your role")
        role = st.radio("Are you a bank or applicant?", ["applicant", "bank"])
        full_name = st.text_input("Full Name", value="Google User")
        phone = st.text_input("Phone Number")

        if st.button("Confirm", key="confirm_role"):
            user = st.session_state.user
            user_id = user.get("id")
            email = user.get("email")

            # Store into session
            st.session_state.role = role
            st.session_state.user["role"] = role
            st.session_state.user["full_name"] = full_name
            st.session_state.user["phone_number"] = phone

            # Load Supabase
            load_dotenv()
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

            # Insert into user_profile table
            profile_data = {
                "user_id": user_id,
                "email": email,
                "role": role,
                "full_name": full_name,
                "phone_number": phone
            }

            try:
                insert_response = supabase.table("user_profile").insert(profile_data).execute()
                if hasattr(insert_response, "error") and insert_response.error:
                    st.error(f"Failed to save profile: {insert_response.error.message}")
                    return
                st.success("Role saved successfully!")
                st.session_state.page = role
                st.rerun()
            except Exception as e:
                st.error(f"Supabase error: {e}")
        return

    # -------------------------------
    # Normal Home Page
    # -------------------------------
    st.title("Welcome to Loanalyze!")
    st.markdown("""
    *Loanalyze* is your smart loan risk analysis & prediction platform — powered by *ML* and *Supabase*.

    - Applicants: Apply & check your loan risk  
    - Banks: Upload client data for analysis  
    - Admins: Manage users & audit records  
    - Public: See aggregated trends  
    """)

    st.subheader("Get Started")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", key="home_login"):
            st.session_state.page = "login"
    with col2:
        if st.button("Register", key="home_register"):
            st.session_state.page = "register"

    st.markdown("---")
    st.info("Contact loanalyzewebapp@gmail.com")
