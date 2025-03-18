import streamlit as st
import requests
import json
import pandas as pd
from config import BASE_API_URL

def show():
    st.title("🍽️ Meal Planning")

    # 1) Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to use Meal Planning.")
        return

    # 2) Load macros from session state if available (from Target Macros or wherever)
    meal_plan_macros = st.session_state.get("meal_plan_macros", {})
    
    default_protein = meal_plan_macros.get("protein", 100)
    default_carbs = meal_plan_macros.get("carbs", 200)
    default_fats = meal_plan_macros.get("fats", 50)

    # 3) Macro Input Section
    st.subheader("📊 Enter Your Target Macros")

    target_protein = st.number_input(
        "Target Protein (g)", min_value=0, step=1, value=int(default_protein)
    )
    target_carbs = st.number_input(
        "Target Carbs (g)", min_value=0, step=1, value=int(default_carbs)
    )
    target_fats = st.number_input(
        "Target Fats (g)", min_value=0, step=1, value=int(default_fats)
    )

    # Automatically calculate calories
    target_calories = (target_protein * 4) + (target_carbs * 4) + (target_fats * 9)
    st.markdown(f"### 🎯 Calculated Target Calories: **{target_calories:.0f} kcal**")

    # 4) Meal Plan Type Selection
    st.subheader("📌 Choose Meal Plan Type")
    meal_plan_type = st.radio(
        "How should the AI generate your meal plan?",
        ["Use my food list", "Suggest own foods"],
        index=0
    )

    # 5) Select number of meals
    num_meals = st.number_input("Select number of meals per day:", min_value=1, max_value=8, value=4)

    # 6) Generate Meal Plan
    if st.button("Generate Meal Plan"):
        with st.spinner("Generating your personalized meal plan..."):

            # If user wants to use their own foods, fetch them
            use_food_list_flag = meal_plan_type == "Use my food list"
            food_prompt = ""
            if use_food_list_flag:
                foods_url = f"{BASE_API_URL}/foods/{user_id}"
                foods_response = requests.get(foods_url)
                if foods_response.status_code == 200:
                    foods = foods_response.json()
                    food_list = "\n".join([
                        f"{f['name']}: {f['calories']} kcal, {f['protein']}g protein, {f['carbs']}g carbs, {f['fats']}g fats"
                        for f in foods
                    ])
                    food_prompt = f"Use only these ingredients:\n{food_list}\n"
                else:
                    st.error(f"❌ Unable to fetch your food list. {foods_response.text}")
                    return
            else:
                food_prompt = "You can freely suggest nutritious ingredients suitable for balanced meals."

            # Build the prompt for the meal plan
            prompt = f"""
            Generate {num_meals} meals for one day. Each meal must:
            - Be either a typical Breakfast, Lunch, Snack or Dinner.
            - Consist of 3 to 8 ingredients with specific gram amounts.
            - Avoid unrealistic meals.
            - Include step-by-step cooking instructions.

            Each meal should meet approximately:
            - Calories: {target_calories / num_meals:.0f} per meal
            - Protein: {target_protein / num_meals:.1f} g
            - Carbs: {target_carbs / num_meals:.1f} g
            - Fats: {target_fats / num_meals:.1f} g

            Format strictly as JSON:
            {{
                "meals": [
                    {{
                        "meal": "Meal Name",
                        "recipe": {{
                            "ingredients": [{{"food": "...", "grams": 0}}],
                            "instructions": "..."
                        }},
                        "calories": 0.0,
                        "protein": 0.0,
                        "carbs": 0.0,
                        "fats": 0.0
                    }}
                ]
            }}
            {food_prompt}
            """.strip()

            # Make request to /generate_meal
            request_body = {"prompt": prompt, "use_food_list": use_food_list_flag}
            response = requests.post(f"{BASE_API_URL}/generate_meal/", json=request_body)

            if response.status_code == 200:
                response_json = response.json()
                meal_plan = response_json.get("meal_plan", {})

                if meal_plan and isinstance(meal_plan, dict) and "meals" in meal_plan:
                    st.subheader("🥗 AI-Generated Meal Plan")

                    for meal_item in meal_plan["meals"]:
                        st.markdown(f"#### 🍽️ {meal_item['meal']}")
                        ingr_df = pd.DataFrame(meal_item['recipe']['ingredients'])
                        st.table(ingr_df)
                        st.write(
                            f"Calories: {meal_item['calories']} | "
                            f"Protein: {meal_item['protein']} | "
                            f"Carbs: {meal_item['carbs']} | "
                            f"Fats: {meal_item['fats']}"
                        )
                        st.write("**Instructions:**", meal_item['recipe']['instructions'])

                else:
                    st.warning("⚠️ Unexpected response structure from backend.")
                    st.json(meal_plan)

            else:
                st.error(f"❌ Failed to generate meal plan. Status code: {response.status_code}")
                st.text(response.text)
