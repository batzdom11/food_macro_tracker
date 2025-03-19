import streamlit as st
import requests
from config import BASE_API_URL

# Define body fat options with labels, images, and corresponding values
body_fat_options = [
    {"label": "<12%", "image": "https://img.freepik.com/free-vector/hand-drawn-human-body-outline-illustration_23-2150611425.jpg?t=st=1742417011~exp=1742420611~hmac=e25bf96a5ec68acda587131770c24146dfa278c76e8626088a470cfbbf4b4606&w=740", "value": 11},
    {"label": "12-15%", "image": "https://img.freepik.com/free-vector/hand-drawn-human-body-outline-illustration_23-2150611431.jpg?t=st=1742416883~exp=1742420483~hmac=c86a21206df3a6903b75238a4ae265c16b44cd7ed6bf750897ad887b29b5740a&w=740", "value": 13.5},
    {"label": "15-18%", "image": "https://img.freepik.com/free-vector/hand-drawn-human-body-outline-illustration_23-2150564974.jpg?t=st=1742417060~exp=1742420660~hmac=573a53c12a0ffed1b7d0302a912fdec0944fbeb955dd364a150c223bc8ab6000&w=740", "value": 16.5},
    {"label": "18-21%", "image": "https://img.freepik.com/free-vector/hand-drawn-human-body-outline-illustration_23-2150564968.jpg?t=st=1742417151~exp=1742420751~hmac=210e474a8d291a67bf24c27819513f6fa53ce58716ba72a68b7788a15edcbe03&w=740", "value": 19.5},
    {"label": "21-25%", "image": "https://img.freepik.com/free-vector/hand-drawn-human-body-outline-illustration_23-2150564971.jpg?t=st=1742417326~exp=1742420926~hmac=c5232a209c43501fbbd00ad2b0c9b545b6e223376b04b042b54d2813a088acdb&w=740", "value": 23},
    {"label": ">25%+", "image": "https://img.freepik.com/free-vector/hand-drawn-human-body-outline-illustration_23-2150611434.jpg?t=st=1742416806~exp=1742420406~hmac=66c58a1037d3b7e3b6b4bcbf2a9ea30ab2a3b37e33bdde8db99e5930ea3d35d6&w=740", "value": 27}
]

def show():
    st.title("🎯 Target Macro Suggestions")

    # Ensure user is logged in
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ You must be logged in to access Target Macros.")
        return

    # Load existing target macros for this user
    existing_data = None
    resp = requests.get(f"{BASE_API_URL}/target_macros/{user_id}")
    if resp.status_code == 200:
        existing_data = resp.json()
    elif resp.status_code != 404:
        st.error(f"❌ Error fetching target macros: {resp.text}")
        return

    # Pre-fill fields if existing data available, else use defaults
    weight_val = existing_data["weight"] if existing_data else 70.0
    height_val = existing_data["height"] if existing_data else 170.0
    body_fat_val = existing_data["body_fat"] if existing_data else 20.0
    activity_lvl = existing_data["activity_level"] if existing_data else "Sedentary (Little to no exercise)"
    goal_val = existing_data["goal"] if existing_data else "Maintain weight, lose fat"
    tdee_val = existing_data["tdee"] if existing_data else 0.0
    target_cals_val = existing_data["target_calories"] if existing_data else 0.0
    prot_val = existing_data["protein"] if existing_data else 0.0
    carbs_val = existing_data["carbs"] if existing_data else 0.0
    fats_val = existing_data["fats"] if existing_data else 0.0

    # Body Stats Inputs
    st.subheader("💪 Enter Your Body Stats")
    weight = st.number_input("Weight (kg)", value=float(weight_val), step=0.1)
    height = st.number_input("Height (cm)", value=float(height_val), step=1.0)

    # Body Fat Selection with Images
    st.subheader("📏 Select Your Approximate Body Fat (%)")
    if "selected_body_fat" not in st.session_state:
        st.session_state["selected_body_fat"] = body_fat_val

    cols = st.columns(len(body_fat_options))
    for idx, (col, option) in enumerate(zip(cols, body_fat_options)):
        col.image(option["image"], caption=option["label"], width=100)
        if col.button(option["label"], key=f"bodyfat_{idx}"):
            st.session_state["selected_body_fat"] = option["value"]

    body_fat = st.session_state["selected_body_fat"]
    st.success(f"Selected body fat: {body_fat}%")

    # Activity Level
    st.subheader("💪 Select Your Activity Level")
    activity_options = [
        "Sedentary (Little to no exercise)",
        "Lightly active (1-3 days/week)",
        "Moderately active (3-5 days/week)",
        "Very active (6-7 days/week)",
        "Super active (Athlete, intense daily workouts)"
    ]
    activity_level = st.selectbox("Activity Level:", options=activity_options, index=activity_options.index(activity_lvl))

    # Goal Selection
    st.subheader("🎯 Select Your Goal")
    goal_options = [
        "Gain weight and muscle",
        "Maintain weight, lose fat",
        "Lose weight and fat",
        "Lose weight at maximum recommended pace"
    ]
    goal = st.radio("Goal:", goal_options, index=goal_options.index(goal_val))

    # Display Existing Macros
    st.write("### Current Calculated Macros:")
    st.write(f"**TDEE:** {tdee_val} kcal/day")
    st.write(f"**Target Calories:** {target_cals_val} kcal/day")
    st.write(f"**Protein:** {prot_val} g/day")
    st.write(f"**Carbs:** {carbs_val} g/day")
    st.write(f"**Fats:** {fats_val} g/day")

    # Calculate, Save and Transfer Macros
    calc_button_col, transfer_button_col = st.columns(2)

    with calc_button_col:
        if st.button("Calculate & Save Target Macros"):
            lbm = weight * (1 - (body_fat / 100.0))
            bmr = 370 + (21.6 * lbm)

            act_map = {activity: mult for activity, mult in zip(activity_options, [1.2, 1.375, 1.55, 1.725, 1.9])}
            new_tdee = bmr * act_map[activity_level]

            goal_multipliers = {goal: mult for goal, mult in zip(goal_options, [1.15, 1.0, 0.85, 0.66])}
            target_cals = round(new_tdee * goal_multipliers[goal])

            new_protein = round(weight * 2.0)
            new_fats = round(target_cals * 0.25 / 9)
            new_carbs = round((target_cals - (new_protein * 4 + new_fats * 9)) / 4)

            payload = {"weight": weight, "height": height, "body_fat": body_fat, "activity_level": activity_level, "goal": goal, "tdee": round(new_tdee), "target_calories": target_cals, "protein": new_protein, "carbs": new_carbs, "fats": new_fats}

            save_url = f"{BASE_API_URL}/target_macros/{user_id}"
            resp = requests.post(save_url, json=payload)
            if resp.status_code == 200:
                st.success("✅ Target Macros Saved/Updated!")
                st.rerun()
            else:
                st.error(f"❌ Error saving macros: {resp.text}")

    with transfer_button_col:
        if st.button("Use These Macros in Meal Planning"):
            st.session_state["meal_plan_macros"] = {"target_calories": target_cals_val, "protein": prot_val, "carbs": carbs_val, "fats": fats_val}
            st.success("Macros transferred to Meal Planning!")

    st.write("*Tip: After transferring macros, go to the Meal Planning page.*")