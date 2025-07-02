import streamlit as st
from supabase import Client
from typing import Callable

def app(supabase: Client, navigate: Callable):
    st.set_page_config(page_title="Register", layout="centered")
    st.title("Register")

    with st.form("register_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        phone_number = st.text_input("Phone Number")
        role = st.selectbox("Role", ["applicant", "bank","admin"])
        submit = st.form_submit_button("Register")

        if submit:
            if not full_name or not email or not password or not phone_number:
                st.error("Please fill in all fields.")
                return

            try:
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })

                user = getattr(auth_response, 'user', None)
                if user is None:
                    st.success("Account created! Please confirm your email before logging in.")
                    return

            except Exception as e:
                st.error(f"Check your mail to confirm.{e}")
