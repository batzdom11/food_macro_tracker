import streamlit as st
import requests

BASE_API_URL = "http://127.0.0.1:8000"

def show():
    st.title("🥗 Food List & Management")

    # 1. Check if user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to view this page.")
        return

    # 2. Build the dynamic URL with the numeric user_id
    foods_api_url = f"{BASE_API_URL}/foods/{user_id}"
    macros_api_url = f"{BASE_API_URL}/get_food_macros/"

    # 3. Fetch current foods
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

    # 4. Display the food list
    if foods:
        st.subheader("📋 Food List")
        for food in foods:
            st.write(f"🍎 {food['name']} - {food['calories']} kcal, "
                     f"{food['protein']}g protein, {food['carbs']}g carbs, {food['fats']}g fats")
    else:
        st.info("No foods available. Add some!")

    # 5. Delete a Food
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

    # 6. Search Food Macros
    st.subheader("🔍 Search Food to Auto-Fill Form")
    food_name = st.text_input("Enter a food name to search:")

    if "food_macros" not in st.session_state:
        st.session_state["food_macros"] = {}

    if st.button("Get Macros"):
        if food_name:
            try:
                response = requests.get(f"{macros_api_url}{food_name}")
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        st.error(data["error"])
                        st.session_state["food_macros"] = {}
                    else:
                        st.session_state["food_macros"] = data
                else:
                    st.error(f"❌ Error fetching macros: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API request failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter a food name.")

    # 7. Add a New Food
    st.subheader("📋 Add a New Food")
    food_macros = st.session_state["food_macros"]

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    calories = st.number_input("Calories (kcal per 100g)", value=safe_float(food_macros.get("calories")), step=1.0)
    protein = st.number_input("Protein (g)", value=safe_float(food_macros.get("protein")), step=0.1)
    carbs = st.number_input("Carbs (g)", value=safe_float(food_macros.get("carbs")), step=0.1)
    fats = st.number_input("Fats (g)", value=safe_float(food_macros.get("fats")), step=0.1)

    if st.button("Add Food"):
        if food_name:
            payload = {
                "name": food_name,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fats": fats
            }
            try:
                resp = requests.post(foods_api_url, json=payload)
                if resp.status_code == 200:
                    st.success(f"✅ {food_name} added successfully!")
                    st.session_state["food_macros"] = {}
                    st.rerun()
                else:
                    # Attempt to parse JSON error
                    try:
                        detail = resp.json().get('detail', 'Unknown error')
                        st.error(f"❌ Error saving food: {detail}")
                    except:
                        st.error(f"❌ Error saving food: {resp.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API request failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter a food name.")
