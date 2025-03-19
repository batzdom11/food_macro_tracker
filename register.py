import streamlit as st
import requests  # also needed for API calls later
from config import BASE_API_URL
#BASE_API_URL = "https://food-macro-tracker.onrender.com"

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
