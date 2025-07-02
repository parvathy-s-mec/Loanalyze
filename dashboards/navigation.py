# navigation.py

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

def go_to_dashboard(role: str):
    """
    Redirect user to their role-based dashboard.
    """
    if role == "applicant":
        switch_page("dashboards/applicant")
    elif role == "bank":
        switch_page("dashboards/bank")
    elif role == "admin":
        switch_page("dashboards/admin")
    else:
        switch_page("dashboards/public")

def logout():
    """
    Clear session and redirect to Home page.
    """
    if "user" in st.session_state:
        del st.session_state["user"]
    switch_page("Home")
