import streamlit as st
import requests

BASE_API_URL = "https://food-macro-tracker.onrender.com"

def show():
    st.title("🎯 Target Macro Suggestions")

    # 1) Ensure the user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to access Target Macros.")
        return

    # 2) Attempt to load existing target macros for this user
    existing_data = None
    resp = requests.get(f"{BASE_API_URL}/target_macros/{user_id}")
    if resp.status_code == 200:
        existing_data = resp.json()
    elif resp.status_code == 404:
        # No record found, so user likely has no saved macros yet
        existing_data = None
    else:
        st.error(f"❌ Error fetching target macros: {resp.text}")
        return

    # 3) Pre-fill fields if we have existing data, else default
    if existing_data:
        weight_val = existing_data["weight"]
        height_val = existing_data["height"]
        body_fat_val = existing_data["body_fat"]
        activity_lvl = existing_data["activity_level"]
        goal_val = existing_data["goal"]
        tdee_val = existing_data["tdee"]
        target_cals_val = existing_data["target_calories"]
        prot_val = existing_data["protein"]
        carbs_val = existing_data["carbs"]
        fats_val = existing_data["fats"]
    else:
        # Default everything
        weight_val = 70.0
        height_val = 170.0
        body_fat_val = 20.0
        activity_lvl = "Sedentary (Little to no exercise)"
        goal_val = "Maintain weight, lose fat"
        tdee_val = 0.0
        target_cals_val = 0.0
        prot_val = 0.0
        carbs_val = 0.0
        fats_val = 0.0

    # 4) Create form fields
    st.subheader("💪 Enter Your Body Stats")
    weight = st.number_input("Weight (kg)", value=float(weight_val), step=0.1)
    height = st.number_input("Height (cm)", value=float(height_val), step=1.0)
    body_fat = st.number_input("Body Fat (%)", value=float(body_fat_val), step=0.1)

    st.subheader("💪 Select Your Activity Level")
    activity_options = [
        "Sedentary (Little to no exercise)",
        "Lightly active (1-3 days/week)",
        "Moderately active (3-5 days/week)",
        "Very active (6-7 days/week)",
        "Super active (Athlete, intense daily workouts)"
    ]
    if activity_lvl not in activity_options:
        activity_lvl = "Sedentary (Little to no exercise)"
    activity_level = st.selectbox("Activity Level:", options=activity_options, index=activity_options.index(activity_lvl))

    st.subheader("🎯 Select Your Goal")
    goal_options = [
        "Gain weight and muscle",
        "Maintain weight, lose fat",
        "Lose weight and fat",
        "Lose weight at maximum recommended pace"
    ]
    if goal_val not in goal_options:
        goal_val = "Maintain weight, lose fat"
    goal = st.radio("Goal:", goal_options, index=goal_options.index(goal_val))

    # 5) Display the existing TDEE & macros (if any)
    st.write("### Current Calculated Macros:")
    st.write(f"**TDEE:** {tdee_val} kcal/day")
    st.write(f"**Target Calories:** {target_cals_val} kcal/day")
    st.write(f"**Protein:** {prot_val} g/day")
    st.write(f"**Carbs:** {carbs_val} g/day")
    st.write(f"**Fats:** {fats_val} g/day")

    # 6) Recalculate + Save
    calc_button_col, transfer_button_col = st.columns(2)

    with calc_button_col:
        if st.button("Calculate & Save Target Macros"):
            # Example TDEE calculation (Katch McArdle)
            lbm = weight * (1 - (body_fat / 100.0))
            bmr = 370 + (21.6 * lbm)

            # Multipliers
            act_map = {
                "Sedentary (Little to no exercise)": 1.2,
                "Lightly active (1-3 days/week)": 1.375,
                "Moderately active (3-5 days/week)": 1.55,
                "Very active (6-7 days/week)": 1.725,
                "Super active (Athlete, intense daily workouts)": 1.9
            }
            activity_mult = act_map.get(activity_level, 1.2)
            new_tdee = bmr * activity_mult

            # Adjust TDEE by goal
            if goal == "Gain weight and muscle":
                target_cals = round(new_tdee * 1.15)
            elif goal == "Lose weight and fat":
                target_cals = round(new_tdee * 0.85)
            elif goal == "Lose weight at maximum recommended pace":
                target_cals = round(new_tdee * 0.66)
            else:  # maintain
                target_cals = round(new_tdee)

            # Basic macros
            new_protein = round(weight * 2.0)
            new_fats = round(target_cals * 0.25 / 9)
            new_carbs = round((target_cals - (new_protein * 4 + new_fats * 9)) / 4)

            payload = {
                "weight": weight,
                "height": height,
                "body_fat": body_fat,
                "activity_level": activity_level,
                "goal": goal,
                "tdee": round(new_tdee),
                "target_calories": target_cals,
                "protein": new_protein,
                "carbs": new_carbs,
                "fats": new_fats
            }

            # POST to /target_macros/{user_id}
            try:
                save_url = f"{BASE_API_URL}/target_macros/{user_id}"
                resp = requests.post(save_url, json=payload)
                if resp.status_code == 200:
                    st.success("✅ Target Macros Saved/Updated!")
                    st.rerun()
                else:
                    st.error(f"❌ Error saving macros: {resp.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {str(e)}")

    with transfer_button_col:
        if st.button("Use These Macros in Meal Planning"):
            """
            Store TDEE & macros in session state so that
            the Meal Planning page can auto-load them.
            """
            st.session_state["meal_plan_macros"] = {
                "target_calories": target_cals_val,
                "protein": prot_val,
                "carbs": carbs_val,
                "fats": fats_val
            }
            st.success("These macros have been transferred to Meal Planning!")


    st.write("*Tip: After transferring macros, go to the Meal Planning page.*")

