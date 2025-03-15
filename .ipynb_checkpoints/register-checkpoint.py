import streamlit as st
import requests  # also needed for API calls later

API_URL = "http://127.0.0.1:8000"

def show():
    st.title("📝 Register")

    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")

    if st.button("Register"):
        response = requests.post(f"{API_URL}/register/", json={"username": username, "password": password})
        
        if response.status_code == 200:
            st.success("Registration successful! Please log in.")
        else:
            st.error(f"Registration failed: {response.text}")
