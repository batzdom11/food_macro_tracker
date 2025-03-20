import streamlit as st
import requests
import json
import pandas as pd
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
    st.title("Meal Planning 🍽️")

    # Inject CSS styling
    st.markdown(border_style, unsafe_allow_html=True)

    # Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to use Meal Planning.")
        return

    # Load macros from session state if available
    meal_plan_macros = st.session_state.get("meal_plan_macros", {})
    
    default_protein = meal_plan_macros.get("protein", 100)
    default_carbs = meal_plan_macros.get("carbs", 200)
    default_fats = meal_plan_macros.get("fats", 50)

    # Target Macros Section
    # Target Macros Section with side-by-side inputs
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Enter Your Target Macros")

        col1, col2, col3 = st.columns(3)

        with col1:
            target_protein = st.number_input(
                "Protein (g)", min_value=0, step=1, value=int(default_protein)
            )

        with col2:
            target_carbs = st.number_input(
                "Carbs (g)", min_value=0, step=1, value=int(default_carbs)
            )

        with col3:
            target_fats = st.number_input(
                "Fats (g)", min_value=0, step=1, value=int(default_fats)
            )

        # Automatically calculate calories below columns
        target_calories = (target_protein * 4) + (target_carbs * 4) + (target_fats * 9)
        st.markdown(f"### Estimated Calories: **{target_calories:.0f} kcal/day**")
        st.markdown("</div>", unsafe_allow_html=True)

    # Meal Plan Type Selection
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Choose Meal Plan Type")
        meal_plan_type = st.radio(
            "How should the AI generate your meal plan?",
            ["Let AI suggest foods", "Use my food list"],
            index=0
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Number of Meals Selection
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Select Number of Meals Per Day")
        num_meals = st.number_input("Meals per day:", min_value=1, max_value=8, value=4)
        st.markdown("</div>", unsafe_allow_html=True)

    # Generate Meal Plan Section
    with st.container():
        st.markdown('<div class="bordered-box">', unsafe_allow_html=True)
        st.subheader("Generate Meal Plan")

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
                - Be either a typical Breakfast, Lunch, Snack, or Dinner.
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
                    meal_plan_raw = response_json.get("meal_plan", "")
                    
                    # If the response is already a dict, assume it's valid JSON
                    if isinstance(meal_plan_raw, dict):
                        meal_plan = meal_plan_raw  # No need to process further
                    
                    # If it's a string, clean and parse it
                    elif isinstance(meal_plan_raw, str):
                        try:
                            # Remove potential triple backticks or extra text
                            meal_plan_cleaned = meal_plan_raw.strip("`").strip()
                            
                            # Extract only the JSON part if extra text is included
                            json_start = meal_plan_cleaned.find("{")
                            json_end = meal_plan_cleaned.rfind("}")
                            if json_start != -1 and json_end != -1:
                                meal_plan_cleaned = meal_plan_cleaned[json_start : json_end + 1]
                            
                            # Parse JSON
                            meal_plan = json.loads(meal_plan_cleaned)
                    
                        except json.JSONDecodeError as e:
                            st.error(f"❌ JSON Parse Error: {str(e)}")
                            st.text(meal_plan_raw)  # Show raw response to debug
                            return  # Stop execution if parsing fails
                    
                    else:
                        st.error("⚠️ Unexpected API response format. Meal plan is neither JSON nor a valid string.")
                        st.json(response_json)  # Debugging output
                        return
                
                    if meal_plan and isinstance(meal_plan, dict) and "meals" in meal_plan:
                        st.subheader("AI-Generated Meal Plan")
                
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
                
                
