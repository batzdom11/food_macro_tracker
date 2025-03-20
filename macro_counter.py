import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from config import BASE_API_URL

# CSS for bordered sections
border_style = """
    <style>
        .bordered-box {
            border: 1px solid #ddd;
            padding: 1px;
            border-radius: 10px;
            margin-bottom: 3px;
            background-color: #f9f9f9;
        }
    </style>
"""

def show():
    st.title("Macro Counter 📊")

    # Inject CSS styling
    st.markdown(border_style, unsafe_allow_html=True)

    # Ensure session state exists
    if "meal_ingredients" not in st.session_state:
        st.session_state["meal_ingredients"] = {}
    if "meal_grams" not in st.session_state:
        st.session_state["meal_grams"] = {}

    # Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to use the Macro Counter.")
        return

    # Fetch food list
    foods_url = f"{BASE_API_URL}/foods/{user_id}"
    foods_response = requests.get(foods_url)
    if foods_response.status_code != 200:
        st.error(f"❌ Could not fetch food list. Server responded with: {foods_response.text}")
        return

    foods = foods_response.json()
    food_options = {food["name"]: food for food in foods}

    # Number of Meals Selection
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Select Number of Meals")

        num_meals = st.number_input(
            "Meals today:", min_value=1, max_value=8, value=4, key="num_meals_input"
        )
        st.session_state["num_meals"] = num_meals
        st.markdown("</div>", unsafe_allow_html=True)

    # Fetch saved meals
    meal_names_url = f"{BASE_API_URL}/meals/names/{user_id}"
    saved_meals_response = requests.get(meal_names_url)
    saved_meal_names = saved_meals_response.json() if saved_meals_response.status_code == 200 else []

    total_macros = {"Calories": 0.0, "Protein": 0.0, "Carbs": 0.0, "Fats": 0.0}

    # Meal Tabs
    meal_tabs = st.tabs([f"Meal {i}" for i in range(1, num_meals + 1)])
    
    for meal_num, tab in enumerate(meal_tabs, start=1):
        with tab:
            st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
            st.subheader(f"Meal {meal_num}")
    
            ingredients_key = f"meal_{meal_num}_ingredients"
            meal_name_key = f"meal_name_{meal_num}"
            load_meal_select_key = f"load_saved_meal_{meal_num}"
            load_button_key = f"btn_load_{meal_num}"
            save_button_key = f"save_meal_btn_{meal_num}"
    
            if ingredients_key not in st.session_state:
                st.session_state[ingredients_key] = []
            if meal_name_key not in st.session_state:
                st.session_state[meal_name_key] = ""
    
            # First row: Meal Name, Load Saved Meal, Load Button
            col1, col2, col3 = st.columns([2, 2, 1])
    
            with col1:
                meal_name_input = st.text_input(
                    "Meal Name:",
                    value=st.session_state[meal_name_key],
                    key=meal_name_key
                )
    
            with col2:
                load_meal_select = st.selectbox(
                    "Load Saved Meal",
                    options=["None"] + saved_meal_names,
                    key=load_meal_select_key
                )
    
            with col3:
                st.write("")  # spacing
                st.write("")  # additional spacing for better alignment
                load_meal_clicked = st.button("Load Meal", key=load_button_key)
    
            # Load meal logic BEFORE multiselect widgets
            if load_meal_clicked and load_meal_select != "None":
                load_meal_url = f"{BASE_API_URL}/meals/{user_id}/{load_meal_select}"
                meal_details_response = requests.get(load_meal_url)
    
                if meal_details_response.status_code == 200:
                    loaded_meal = meal_details_response.json()
                    st.success(f"✅ {load_meal_select} loaded.")
    
                    st.session_state[ingredients_key] = [item["food_name"] for item in loaded_meal]
                    for item in loaded_meal:
                        gram_key = f"grams_{meal_num}_{item['food_name']}"
                        st.session_state[gram_key] = float(item["grams"])
                    st.session_state[meal_name_key] = load_meal_select
    
                    st.rerun()
                else:
                    st.error(f"❌ Error loading meal: {meal_details_response.text}")
    
            # Ingredient Selection
            selected_ingredients = st.multiselect(
                f"Select Ingredients for Meal {meal_num}",
                options=list(food_options.keys()),
                default=st.session_state[ingredients_key],
                key=ingredients_key
            )
    
            meal_data = []
    
            for ingredient in selected_ingredients:
                gram_key = f"grams_{meal_num}_{ingredient}"
                if gram_key not in st.session_state:
                    st.session_state[gram_key] = 100.0
    
                grams = st.number_input(
                    f"Grams of {ingredient}",
                    min_value=0.0,
                    step=10.0,
                    value=st.session_state[gram_key],
                    key=gram_key
                )
    
                macros = {
                    "food_name": ingredient,
                    "grams": grams,
                    "calories": (food_options[ingredient]["calories"] * grams) / 100,
                    "protein": (food_options[ingredient]["protein"] * grams) / 100,
                    "carbs": (food_options[ingredient]["carbs"] * grams) / 100,
                    "fats": (food_options[ingredient]["fats"] * grams) / 100,
                }
                meal_data.append(macros)
    
                total_macros["Calories"] += macros["calories"]
                total_macros["Protein"] += macros["protein"]
                total_macros["Carbs"] += macros["carbs"]
                total_macros["Fats"] += macros["fats"]
    
            # Save Meal button at the bottom
            if st.button("Save Meal", key=save_button_key):
                final_meal_name = meal_name_input.strip()
                if not final_meal_name:
                    st.warning("⚠️ Please provide a meal name.")
                else:
                    meal_create_list = [
                        {
                            "meal_name": final_meal_name,
                            "food_name": item["food_name"],
                            "grams": item["grams"],
                            "protein": item["protein"],
                            "carbs": item["carbs"],
                            "fats": item["fats"]
                        }
                        for item in meal_data
                    ]
    
                    save_meal_url = f"{BASE_API_URL}/save_meal/{user_id}"
                    try:
                        resp = requests.post(save_meal_url, json=meal_create_list)
                        if resp.status_code == 200:
                            st.success(f"✅ Meal '{final_meal_name}' saved successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error saving meal: {resp.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Request failed: {str(e)}")
    
            st.markdown("</div>", unsafe_allow_html=True)


    # Daily Macro Summary
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Daily Macro Summary")
        st.write(f"🔥 **Calories:** {total_macros['Calories']:.1f} kcal")
        st.write(f"💪 **Protein:**  {total_macros['Protein']:.1f} g")
        st.write(f"🍞 **Carbs:**    {total_macros['Carbs']:.1f} g")
        st.write(f"🥑 **Fats:**     {total_macros['Fats']:.1f} g")
        st.markdown("</div>", unsafe_allow_html=True)

    # Macro Breakdown Chart
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Macro Breakdown")

        df = pd.DataFrame({"Macro": ["Protein", "Carbs", "Fats"], "Amount_g": [total_macros[m] for m in ["Protein", "Carbs", "Fats"]]})
        fig = px.bar(df, x="Macro", y="Amount_g", title="Daily Macronutrient Breakdown", labels={"Amount_g": "Grams"}, color="Macro")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
