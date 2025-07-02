import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

# --------------------------
# Load Supabase credentials
# --------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Page Config
# --------------------------
st.set_page_config(page_title="User Management", layout="wide")
st.title("User Management Panel")

# --------------------------
# Fetch user data
# --------------------------
response = supabase.table("user_profile").select("*").execute()
users = response.data

if not users:
    st.info("No users found.")
else:
    df = pd.DataFrame(users)

    roles = df["role"].dropna().unique().tolist()
    selected_role = st.selectbox("Filter by Role", ["All"] + roles)
    if selected_role != "All":
        df = df[df["role"] == selected_role]

    st.dataframe(df)

    # --------------------------
    # Update user role
    # --------------------------
    st.subheader("Update User Role")
    email_to_update = st.selectbox("Select User by Email", df["email"].tolist(), key="update")
    new_role = st.selectbox("New Role", ["applicant", "admin", "bank", "public"], key="role")

    if st.button("Update Role"):
        user_id = df[df["email"] == email_to_update]["user_id"].values[0]
        result = supabase.table("user_profile").update({"role": new_role}).eq("user_id", user_id).execute()
        if result.get("error"):
            st.error(f"Failed to update role: {result['error']['message']}")
        else:
            st.success(f"Role updated to '{new_role}' for {email_to_update}")
            st.experimental_rerun()

    # --------------------------
    # Delete user (use with caution!)
    # --------------------------
    with st.expander("Delete User (Danger Zone)"):
        email_to_delete = st.selectbox("Select User to Delete", df["email"].tolist(), key="delete")
        if st.button("Delete User"):
            user_id = df[df["email"] == email_to_delete]["user_id"].values[0]
            supabase.table("user_profile").delete().eq("user_id", user_id).execute()
            st.warning(f"User {email_to_delete} deleted. Refresh the page to update the list.")

st.markdown("---")
st.caption("Loanalyze • User Management Page • Streamlit + Supabase")
