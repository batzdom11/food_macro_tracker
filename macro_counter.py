import streamlit as st
import requests
import pandas as pd
#import matplotlib.pyplot as plt
import plotly.express as px
from config import BASE_API_URL


BASE_API_URL = "https://5aaresabhb.eu.loclx.io"

def show():
    st.title("📊 Macro Counter")
    
    # Ensure session state exists for meal ingredients
    if "meal_ingredients" not in st.session_state:
        st.session_state["meal_ingredients"] = {}
        
    # Ensure session state exists for meal ingredient grams
    if "meal_grams" not in st.session_state:
        st.session_state["meal_grams"] = {}  # Stores gram amounts for each meal

    # 1) Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to use the Macro Counter.")
        return

    # 2) Fetch the user’s food list (substituting user_id)
    foods_url = f"{BASE_API_URL}/foods/{user_id}"
    foods_response = requests.get(foods_url)
    if foods_response.status_code != 200:
        st.error(f"❌ Could not fetch food list. Server responded with: {foods_response.text}")
        return

    foods = foods_response.json()
    # Create a dictionary for quick lookups: {food_name: {... macros ...}}
    food_options = {food["name"]: food for food in foods}

    # 3) Store number of meals in session_state
    # Ensure session state exists for num_meals
    if "num_meals" not in st.session_state:
        st.session_state["num_meals"] = 4  # Default in case API fails
    
    # Fetch stored num_meals from backend
    num_meals_url = f"{BASE_API_URL}/get_num_meals/{user_id}"
    num_meals_response = requests.get(num_meals_url)
    if num_meals_response.status_code == 200:
        st.session_state["num_meals"] = num_meals_response.json().get("num_meals", 4)

    
    num_meals = st.number_input(
        "🍽️ Select number of meals today:", 
        min_value=1, max_value=8, 
        value=st.session_state["num_meals"], 
        key="num_meals_input"
    )
    
    # Update session state when user changes selection
    if num_meals != st.session_state["num_meals"]:
        st.session_state["num_meals"] = num_meals
        st.rerun()  # Ensures tabs update immediately


    # 4) Fetch saved meal names from the user’s meals
    meal_names_url = f"{BASE_API_URL}/meals/names/{user_id}"
    saved_meals_response = requests.get(meal_names_url)
    saved_meal_names = saved_meals_response.json() if saved_meals_response.status_code == 200 else []

    # 5) Keep track of overall daily totals
    total_macros = {"Calories": 0.0, "Protein": 0.0, "Carbs": 0.0, "Fats": 0.0}

    # Create tab views for each meal
    meal_tabs = st.tabs([f"Meal {i}" for i in range(1, st.session_state["num_meals"] + 1)])


    for meal_num, tab in enumerate(meal_tabs, start=1):
        with tab:
            st.markdown(f"### 🍽️ Meal {meal_num}")

            # A text field so user can name this meal
            meal_name = st.text_input(f"Meal {meal_num} Name:", key=f"meal_name_{meal_num}")

            # Load meal section
            load_meal_select = st.selectbox(
                f"Load a Saved Meal for Meal {meal_num}",
                options=["None"] + saved_meal_names,
                key=f"load_saved_meal_{meal_num}"
            )

            if st.button(f"Load Meal {meal_num}", key=f"btn_load_{meal_num}") and load_meal_select != "None":
                # Build the URL: /meals/{user_id}/{meal_name}
                load_meal_url = f"{BASE_API_URL}/meals/{user_id}/{load_meal_select}"
                meal_details_response = requests.get(load_meal_url)
                if meal_details_response.status_code == 200:
                    loaded_meal = meal_details_response.json()
                    st.success(f"✅ {load_meal_select} loaded.")

                    # Populate session_state with loaded data
                    # So the user can see them in the multi-select and input fields
                    st.session_state[f"meal_{meal_num}_ingredients"] = [item["food_name"] for item in loaded_meal]
                    for item in loaded_meal:
                        # We'll store grams in session state so it auto-populates
                        st.session_state[f"grams_{meal_num}_{item['food_name']}"] = float(item["grams"])

                    # Rerun to reflect changes
                    st.rerun()
                else:
                    st.error(f"❌ Error loading meal: {meal_details_response.text}")

            # Ensure this meal has an entry in session_state
            if meal_num not in st.session_state["meal_ingredients"]:
                st.session_state["meal_ingredients"][meal_num] = []
            
            # Let user choose ingredients
            selected_ingredients = st.multiselect(
                f"Select ingredients for Meal {meal_num}",
                options=list(food_options.keys()),
                default=st.session_state["meal_ingredients"].get(meal_num, []),  # Load previous selection
                key=f"meal_{meal_num}_ingredients"
            )
            
            # Update session state when selection changes
            if selected_ingredients != st.session_state["meal_ingredients"].get(meal_num, []):
                st.session_state["meal_ingredients"][meal_num] = selected_ingredients


            meal_data = []

            # Ensure this meal has an entry in session_state
            if meal_num not in st.session_state["meal_grams"]:
                st.session_state["meal_grams"][meal_num] = {}
            
            meal_grams_state = st.session_state["meal_grams"][meal_num]  # Shortcut for readability
            
            # Loop through selected ingredients
            for ingredient in selected_ingredients:
                # Ensure this ingredient has an entry in session_state
                if ingredient not in meal_grams_state:
                    meal_grams_state[ingredient] = 100.0  # Default to 100g
            
                # Input field for grams
                grams = st.number_input(
                    f"Grams of {ingredient}",
                    min_value=0.0,
                    step=10.0,
                    value=float(meal_grams_state[ingredient]),
                    key=f"grams_{meal_num}_{ingredient}"
                )
            
                # Update session state when grams change
                if grams != meal_grams_state[ingredient]:
                    meal_grams_state[ingredient] = grams

                # Calc macros
                macros = {
                    "food_name": ingredient,
                    "grams": grams,
                    "calories": (food_options[ingredient]["calories"] * grams) / 100,
                    "protein": (food_options[ingredient]["protein"] * grams) / 100,
                    "carbs":   (food_options[ingredient]["carbs"]   * grams) / 100,
                    "fats":    (food_options[ingredient]["fats"]    * grams) / 100,
                }
                meal_data.append(macros)

                meal_protein = sum(item['protein'] for item in meal_data)
                meal_carbs   = sum(item['carbs'] for item in meal_data)
                meal_fats    = sum(item['fats'] for item in meal_data)
                
                # Add to daily total
                total_macros["Calories"] += macros["calories"]
                total_macros["Protein"]  += macros["protein"]
                total_macros["Carbs"]    += macros["carbs"]
                total_macros["Fats"]     += macros["fats"]

            # Save meal button
            if st.button(f"💾 Save Meal {meal_num}", key=f"save_meal_btn_{meal_num}"):
                if not meal_name:
                    st.warning(f"⚠️ Please provide a meal name for Meal {meal_num}.")
                else:
                    # Convert meal_data to the format needed by /save_meal/{user_id}
                    # Each item must be a dict with keys:
                    #   meal_name, food_name, grams, protein, carbs, fats
                    # We'll create a list of MealCreate-like dicts
                    meal_create_list = []
                    for item in meal_data:
                        meal_create_list.append({
                            "meal_name": meal_name,
                            "food_name": item["food_name"],
                            "grams":     item["grams"],
                            "protein":   item["protein"],
                            "carbs":     item["carbs"],
                            "fats":      item["fats"]
                        })

                    # POST to /save_meal/{user_id}
                    save_meal_url = f"{BASE_API_URL}/save_meal/{user_id}"
                    try:
                        resp = requests.post(save_meal_url, json=meal_create_list)
                        if resp.status_code == 200:
                            st.success(f"✅ Meal '{meal_name}' saved successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error saving meal: {resp.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Request failed: {str(e)}")
   

    # Summaries of daily macros
    st.subheader("📋 Daily Macro Summary")
    st.write(f"**Calories:** {total_macros['Calories']:.1f} kcal")
    st.write(f"**Protein:**  {total_macros['Protein']:.1f} g")
    st.write(f"**Carbs:**    {total_macros['Carbs']:.1f} g")
    st.write(f"**Fats:**     {total_macros['Fats']:.1f} g")

    # Create a bar chart for macros (excluding calories)
    st.subheader("📊 Daily Macro Breakdown")
    macro_names = ["Protein", "Carbs", "Fats"]
    macro_values = [total_macros[m] for m in macro_names]

    # Create a DataFrame
    df = pd.DataFrame({
        "Macro": macro_names,
        "Amount_g": macro_values
    })
    
    # Define distinct colors for each bar
    color_map = {
        "Protein": "salmon",
        "Carbs": "lightblue",
        "Fats": "lightgreen"
    }
    
    # Create a bar chart with color="Macro" and our custom color_map
    fig = px.bar(
        df,
        x="Macro",
        y="Amount_g",
        title="Daily Macronutrient Breakdown",
        labels={"Amount_g": "Grams"},  # rename axis
        color="Macro",
        color_discrete_map=color_map,
    )
    
    # Remove default “Macro” tooltip line, and show only the numeric value + “g”
    fig.update_traces(
        hovertemplate="%{y:.0f}g",  # e.g. "182.55g"
        # If you also want to hide the 'Macro=<x>' line from the tooltip:
        hoverinfo="none"  # or you can remove/hide items from “hoverdata”
    )
    
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)





   