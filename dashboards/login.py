import streamlit as st
from supabase import Client
from typing import Callable

def app(supabase: Client, navigate: Callable):
    st.set_page_config(page_title="Login", layout="centered")
    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.error("Please enter both email and password.")
            return

        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            user = getattr(auth_response, 'user', None)
            if not user:
                st.error("Login failed: Invalid credentials.")
                return

            user_id = user.id

            # Fetch user_profile
            profile_response = supabase.table("user_profile").select("*").eq("user_id", user_id).execute()

            if profile_response.data:
                profile = profile_response.data[0]
                st.session_state['user'] = profile
                st.session_state['role'] = profile['role']
                st.success(f"Welcome, {profile['full_name']}!")

                navigate(profile['role'])
                st.rerun()

            else:
                # Store minimal user info to session and redirect to select role
                st.session_state['user_auth'] = {
                    "id": user_id,
                    "email": email
                }
                navigate("select_role")
                st.rerun()

        except Exception as e:
            st.error(f"Login failed: {e}")
