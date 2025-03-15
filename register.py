import streamlit as st
import requests  # also needed for API calls later

BASE_API_URL = "https://5aaresabhb.eu.loclx.io"

def show():
    st.title("📝 Register")

    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")

    if st.button("Register"):
        response = requests.post(f"{BASE_API_URL}/register/", json={"username": username, "password": password})
        
        if response.status_code == 200:
            st.success("Registration successful! Please log in.")
        else:
            st.error(f"Registration failed: {response.text}")
