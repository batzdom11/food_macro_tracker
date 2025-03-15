import streamlit as st
import requests

API_URL = "https://food-macro-tracker.onrender.com"

def show():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        response = requests.post(f"{API_URL}/login/", json={"username": username, "password": password})
        
        if response.status_code == 200:
            user_data = response.json()
            st.session_state['user_id'] = user_data['id']
            st.session_state['username'] = username
            st.rerun()
        else:
            st.error("Login failed. Please check your credentials.")
