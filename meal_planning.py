import streamlit as st
import requests
import json  # This is missing, causing the error
from config import BASE_API_URL

def show():
    st.title("🍽️ Meal Planning")

    # 1) Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to use Meal Planning.")
        return

    # 2) Load macros from session state if available (from Target Macros or wherever)
    # Provide defaults if they're not set
    meal_plan_macros = st.session_state.get("meal_plan_macros", {})
    # Or if you used 'target_macros' dict in session:
    # meal_plan_macros = st.session_state.get("target_macros", {})
    
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

            # If user wants to use their own foods, fetch them from /foods/{user_id}
            if meal_plan_type == "Use my food list":
                foods_url = f"{BASE_API_URL}/foods/{user_id}"
                foods_response = requests.get(foods_url)
                if foods_response.status_code == 200:
                    foods = foods_response.json()
                    food_list = "\n".join([
                        f"{f['name']}: {f['calories']} kcal, {f['protein']}g protein, {f['carbs']}g carbs, {f['fats']}g fats"
                        for f in foods
                    ])
                    food_prompt = f"Use only these ingredients:\n{food_list}\n"
                    use_food_list_flag = True
                else:
                    st.error(f"❌ Unable to fetch your food list. {foods_response.text}")
                    return
            else:
                food_prompt = "You can freely suggest nutritious ingredients suitable for balanced meals."
                use_food_list_flag = False

            # Build the prompt for the meal plan
            prompt = f"""
            Generate {num_meals} meals for one day. Each meal must:
            - Be either a typical Breakfast, a typical Lunch, a typical Snack or a typical Dinner.
            - Consist of 3 to 8 ingredients with specific gram amounts.
            - Avoid unrealistic meals.
            - Include step-by-step cooking instructions.

            Each meal should meet approximately:
            - Calories: {target_calories / num_meals:.0f} per meal
            - Protein: {target_protein / num_meals:.1f} g
            - Carbs: {target_carbs / num_meals:.1f} g
            - Fats: {target_fats / num_meals:.1f} g

            Format the response strictly as JSON with keys:
            {{
                "meals": [
                    {{
                        "meal": "Meal Name",
                        "recipe": {{
                            "ingredients": [{{"food": "...", "grams": 0}}],
                            "instructions": "Step-by-step instructions"
                        }},
                        "calories": 0.0,
                        "protein": 0.0,
                        "carbs": 0.0,
                        "fats": 0.0
                    }}
                ]
            }}
            Return only valid JSON, with no triple backticks or code fences. No disclaimers.
            {food_prompt}
            """.strip()

            # Make request to /generate_meal
            request_body = {
                "prompt": prompt,
                "use_food_list": use_food_list_flag
            }
            response = requests.post(
                f"{BASE_API_URL}/generate_meal/",
                json=request_body
            )

            if response.status_code == 200:
                response_json = response.json()
                meal_plan = response_json.get("meal_plan", "")
            
                try:
                    meal_data = json.loads(meal_plan)  # Convert JSON string to Python dict
                except (json.JSONDecodeError, TypeError) as e:
                    st.warning(f"⚠️ Could not parse JSON from meal plan: {str(e)}")
                    st.text(meal_plan)
                    return  # Stop execution if JSON is not valid
               
                if meal_data:
                    st.subheader("🥗 AI-Generated Meal Plan")
            
                    import pandas as pd
                                                        
                    # Show each meal in a separate "section":
                    for meal_item in meal_data["meals"]:
                        st.markdown(f"#### 🍽️ {meal_item['meal']}")
                        ingr_df = pd.DataFrame(meal_item['recipe']['ingredients'])
                        st.table(ingr_df)
                        st.write(f"Calories: {meal_item['calories']} | Protein: {meal_item['protein']} | Carbs: {meal_item['carbs']} | Fats: {meal_item['fats']}")
                        st.write("**Instructions:**", meal_item['recipe']['instructions'])
                else:
                    st.write("No 'meals' key found in JSON, showing raw text:")
                    st.write(meal_plan)

                
                import json
                                
                try:
                    # Convert the string meal_plan into a Python dict
                    meal_data = json.loads(meal_plan)  # Expecting {"meals": [...], ...}
                
                    # Show structured tables
                    if "meals" in meal_data:
                        # Option A: Single big table for all meals/ingredients
                        df_rows = []
                        for meal_item in meal_data["meals"]:
                            meal_name = meal_item.get("meal", "")
                            instructions = meal_item.get("recipe", {}).get("instructions", "")
                            meal_cals = meal_item.get("calories", 0.0)
                            meal_prot = meal_item.get("protein", 0.0)
                            meal_carbs = meal_item.get("carbs", 0.0)
                            meal_fats = meal_item.get("fats", 0.0)
                
                            # For each ingredient in recipe
                            ingredients_list = meal_item.get("recipe", {}).get("ingredients", [])
                            for ingr in ingredients_list:
                                df_rows.append({
                                    "Meal": meal_name,
                                    "Food": ingr.get("food", ""),
                                    "Grams": ingr.get("grams", 0),
                                    "Calories": meal_cals,
                                    "Protein": meal_prot,
                                    "Carbs": meal_carbs,
                                    "Fats": meal_fats,
                                    "Instructions": instructions
                                })
                
                        import pandas as pd
                                                    
                        # Show each meal in a separate "section":
                        for meal_item in meal_data["meals"]:
                            st.markdown(f"#### 🍽️ {meal_item['meal']}")
                            ingr_df = pd.DataFrame(meal_item['recipe']['ingredients'])
                            st.table(ingr_df)
                            st.write(f"Calories: {meal_item['calories']} | Protein: {meal_item['protein']} | Carbs: {meal_item['carbs']} | Fats: {meal_item['fats']}")
                            st.write("**Instructions:**", meal_item['recipe']['instructions'])
                
                    else:  # This "else" belongs to "if 'meals' in meal_data"
                        st.write("No 'meals' key found in JSON, showing raw text:")
                        st.write(meal_plan)
                
                except json.JSONDecodeError:
                    st.warning("⚠️ Could not parse JSON from meal plan. Showing raw text:")
                    st.text(meal_plan)
                
                except Exception as e:  # Catch any other unexpected errors
                    st.error(f"❌ An unexpected error occurred: {str(e)}")
                
                # This "else" at the bottom was wrongly placed before.
                if not meal_data:
                    st.error("❌ Received empty meal plan.")
