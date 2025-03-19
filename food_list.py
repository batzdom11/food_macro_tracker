import streamlit as st
import requests
import pandas as pd
from config import BASE_API_URL


def show():
    st.title("🥗 Food List & Management")

    # Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to view this page.")
        return

    foods_api_url = f"{BASE_API_URL}/foods/{user_id}"
    macros_api_url = f"{BASE_API_URL}/get_food_macros/"

    # Fetch current foods
    def get_food_list():
        try:
            response = requests.get(foods_api_url)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API request failed: {str(e)}")
            return []

    foods = get_food_list()

    # Display the food list as a DataFrame for better structure
    st.subheader("📋 Your Food List")
    if foods:
        df_foods = pd.DataFrame(foods)
        df_display = df = df = foods if foods else []
        df = pd.DataFrame(df_rows := [{
            "Name": food['name'],
            "Calories": food['calories'],
            "Protein (g)": food['protein'],
            "Carbs (g)": food['carbs'],
            "Fats (g)": food['fats']
        } for food in foods])

        st.dataframe(df, use_container_width=True)
    else:
        st.info("No foods available. Add some below!")

    # Delete a Food
    st.subheader("🗑️ Delete a Food")
    food_to_delete = st.selectbox("Select a food to delete", [f["name"] for f in foods] if foods else [])

    if st.button("Delete Food"):
        if food_to_delete:
            try:
                response = requests.delete(f"{BASE_API_URL}/foods/{user_id}/{food_to_delete}")
                if response.status_code == 200:
                    st.success(f"✅ {food_to_delete} deleted successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API request failed: {str(e)}")
        else:
            st.warning("⚠️ No food selected.")

    # Search and auto-fill macros
    st.subheader("🔍 Search Food Macros")
    search_food_name = st.text_input("Enter a food name to search:")

    if st.button("Search Macros"):
        if search_food_name:
            try:
                response = requests.get(f"{macros_api_url}{food_name}")
                if response.status_code == 200:
                    st.session_state["food_macros"] = response.json()
                    st.success(f"✅ Macros for {food_name} loaded.")
                else:
                    st.error(f"❌ Error fetching macros: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API request failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter a food name.")

    # Add New Food
    st.subheader("➕ Add a New Food")
    food_macros = st.session_state.get("food_macros", {})

    new_food_name = st.text_input("Food Name", value=search_food_name)
    calories = st.number_input("Calories (kcal per 100g)", value=float(food_macros.get("calories", 0.0)), step=1.0)
    protein = st.number_input("Protein (g)", value=float(food_macros.get("protein", 0.0)), step=0.1)
    carbs = st.number_input("Carbs (g)", value=float(food_macros.get("carbs", 0.0)), step=0.1)
    fats = st.number_input("Fats (g)", value=float(food_macros.get("fats", 0.0)), step=0.1)

    if st.button("Add Food"):
        if new_food_name:
            payload = {
                "name": new_food_name,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fats": fats
            }
            try:
                resp = requests.post(foods_api_url, json=payload)
                if resp.status_code == 200:
                    st.success(f"✅ {new_food_name} added successfully!")
                    st.session_state["food_macros"] = {}
                    st.rerun()
                else:
                    detail = resp.json().get('detail', 'Unknown error')
                    st.error(f"❌ Error saving food: {detail}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API request failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter a food name.")