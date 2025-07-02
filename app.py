import streamlit as st
import os
from supabase import create_client
from dotenv import load_dotenv

# Load env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Session defaults
if "page" not in st.session_state:
    st.session_state.page = "home"

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

# Navigation
def navigate(page):
    st.session_state.page = page.lower()

def logout():
    st.session_state.clear()
    navigate("home")

# Sidebar
with st.sidebar:
    st.title("Loanalyze")
    if st.session_state.user:
        st.write(f"{st.session_state.user['email']}")
        st.write(f"{st.session_state.role}")
        if st.button("Logout", key="sidebar_logout"):
            logout()
    else:
        if st.button("Home", key="sidebar_home"):
            navigate("home")
        if st.button("Login", key="sidebar_login"):
            navigate("login")
        if st.button("Register", key="sidebar_register"):
            navigate("register")
    st.markdown("---")
    if st.button("Public Dashboard", key="sidebar_public"):
        navigate("public")

# Routing
page = st.session_state.page

if page == "home":
    import Home; Home.app(navigate)
elif page == "login":
    import dashboards.login as login; login.app(supabase, navigate)
elif page == "register":
    import dashboards.register as register; register.app(supabase, navigate)
elif page == "select_role":
    import dashboards.select_role as select_role; select_role.app(supabase, navigate)
elif page == "applicant":
    import dashboards.applicant as applicant; applicant.app(supabase)
elif page == "bank":
    import dashboards.bank as bank; bank.app(supabase)
elif page == "admin":
    import dashboards.admin as admin; admin.app(supabase)
elif page == "public":
    import dashboards.public as public; public.app(supabase)
else:
    st.error("Page not found.")
