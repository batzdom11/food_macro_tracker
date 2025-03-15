import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("🥗 Food Macro Tracker")

# --- Search for Food and Auto-Fill Form ---
st.subheader("🔍 Search Food to Auto-Fill Form")

food_name = st.text_input("Enter a food name to search:")
food_macros = None

if st.button("Get Macros"):
    if food_name:
        response = requests.get(f"{API_URL}/get_food_macros/{food_name}")
        if response.status_code == 200:
            food_macros = response.json()
            if "error" in food_macros:
                st.error(food_macros["error"])
                food_macros = None
        else:
            st.error("Error fetching macros. Try again.")
    else:
        st.warning("Please enter a food name.")

# Store the selected food's macros in session state
if "food_macros" not in st.session_state:
    st.session_state.food_macros = None

if food_macros:
    st.session_state.food_macros = food_macros  # Save macros for later use

# --- Add New Food Form (Auto-Filled from Search) ---
st.subheader("📋 Add a New Food")

# Default values (empty or from search)
calories = st.number_input("Calories (kcal per 100g)", value=float(st.session_state.food_macros.get("calories", 0) if st.session_state.food_macros else 0), step=1.0)
protein = st.number_input("Protein (g)", value=float(st.session_state.food_macros.get("protein", 0) if st.session_state.food_macros else 0), step=0.1)
carbs = st.number_input("Carbs (g)", value=float(st.session_state.food_macros.get("carbs", 0) if st.session_state.food_macros else 0), step=0.1)
fats = st.number_input("Fats (g)", value=float(st.session_state.food_macros.get("fats", 0) if st.session_state.food_macros else 0), step=0.1)

if st.button("Add Food"):
    if food_name:
        food_data = {
            "name": food_name,
            "calories": float(calories),
            "protein": float(protein),
            "carbs": float(carbs),
            "fats": float(fats)
        }

        save_response = requests.post(f"{API_URL}/foods/", json=food_data)

        if save_response.status_code == 200:
            st.success(f"✅ {food_name} added successfully!")
            st.session_state.food_macros = None  # Reset form after save
        else:
            st.error(f"❌ Error saving food: {save_response.json().get('detail', 'Unknown error')}")
    else:
        st.warning("Please enter a food name.")

# --- Display Existing Foods ---
st.subheader("📋 Food List")
response = requests.get(f"{API_URL}/foods/")
#st.write("API Response:", response.text)  # Debugging
try:
    foods = response.json()
    if foods:
        for food in foods:
            st.write(
                f"🍎 **{food['name']}** - {food['calories']} kcal, "
                f"{food['protein']}g P, {food['carbs']}g C, {food['fats']}g F"
            )
    else:
        st.write("No foods added yet.")
except requests.exceptions.JSONDecodeError:
    st.error("Error: API returned invalid data.")

# --- Delete a Food Item ---
st.subheader("🗑️ Delete a Food")
food_to_delete = st.selectbox("Select a food to delete", [f["name"] for f in foods] if foods else [])

if st.button("Delete Food"):
    if food_to_delete:
        response = requests.delete(f"{API_URL}/foods/{food_to_delete}")
        if response.status_code == 200:
            st.success(f"{food_to_delete} deleted successfully!")
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    else:
        st.warning("No food selected.")

# --- Generate Meal Plan (New Section at the Bottom) ---
st.subheader("🍽️ AI Meal Planner")

st.subheader("Enter Your Target Macros")
target_calories = st.number_input("Target Calories", min_value=0.0, step=50.0)
target_protein = st.number_input("Target Protein (g)", min_value=0.0, step=1.0)
target_carbs = st.number_input("Target Carbs (g)", min_value=0.0, step=1.0)
target_fats = st.number_input("Target Fats (g)", min_value=0.0, step=1.0)

if st.button("Generate Meal Plan"):
    target_macros = {
        "calories": target_calories,
        "protein": target_protein,
        "carbs": target_carbs,
        "fats": target_fats
    }

    with st.spinner("Generating meal plan..."):
        response = requests.post(f"{API_URL}/generate_meal/", json=target_macros)

    try:
        if response.status_code == 200:
            meal_plan = response.json()
            if "error" in meal_plan:
                st.error(f"❌ Error: {meal_plan['error']}")
            else:
                st.subheader("🥗 AI-Generated Meal Plan")
                for meal in meal_plan["meals"]:
                    st.write(f"🍽️ **{meal['meal']}**")
                    st.write(f"**Ingredients:** {', '.join([f"{item['grams']}g {item['food']}" for item in meal['recipe']['ingredients']])}")
                    st.write(f"**Instructions:** {meal['recipe']['instructions']}")
                    st.write("---")
        else:
            st.error(f"❌ API Error: {response.text}")

    except requests.exceptions.JSONDecodeError:
        st.error("❌ Unexpected API response (not JSON).")



