import streamlit as st
from supabase import Client
from typing import Callable

def app(supabase: Client, navigate: Callable):
    st.set_page_config(page_title="Choose Role", layout="centered")
    st.title("Choose Your Role")

    user = st.session_state.get("user_auth")
    if not user:
        st.error("No user found in session. Please log in first.")
        return

    email = user.get("email")
    user_id = user.get("id")

    role = st.radio("Select your role:", ["applicant", "bank", "admin"])
    full_name = st.text_input("Full Name")
    phone_number = st.text_input("Phone Number")

    if st.button("Continue"):
        if not full_name or not phone_number:
            st.error("Please fill in all fields.")
            return

        profile_data = {
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "phone_number": phone_number,
            "role": role
        }

        try:
            insert_response = supabase.table("user_profile").insert(profile_data).execute()

            if hasattr(insert_response, "error") and insert_response.error:
                st.error(f"Database error: {insert_response.error.message}")
                return

            st.session_state["user"] = profile_data
            st.session_state["role"] = role
            st.success("Profile saved!")

            navigate(role)
            st.rerun()

        except Exception as e:
            st.error(f"Failed to save profile: {e}")
