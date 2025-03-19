import streamlit as st
import login
import register
import food_list
import meal_planning
import macro_counter
import target_macros

# Configure page
st.set_page_config(page_title="🍽️ Food Macro Tracker")

# Initialize pages dictionary
PAGES = {
    "🔐 Login": login,
    "📝 Register": register,
    "📋 My Foods List": food_list,
    "🍽️ AI Meal Suggestions": meal_planning,
    "📊 Daily Macro Counter": macro_counter,
    "🎯 Target Macros": target_macros
}

# Check login state
user_logged_in = st.session_state.get("user_id")

# Determine available pages based on login status
if user_logged_in:
    available_pages = ["🎯 Target Macros", "🍽️ AI Meal Suggestions", "📊 Daily Macro Counter", "📋 My Foods List"]
else:
    available_pages = ["🔐 Login", "📝 Register"]

# Display tabs at the bottom
selected_tab = st.tabs(available_pages)

# Render page content
for tab, page_name in zip(selected_tab, available_pages):
    with tab:
        PAGES[page_name].show()

# Optional logout sidebar (can be removed later)
if user_logged_in:
    st.sidebar.success(f"👤 Logged in as **{st.session_state['username']}**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()
