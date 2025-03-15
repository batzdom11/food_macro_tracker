import streamlit as st
import login
import register
import food_list
import meal_planning
import macro_counter
import target_macros

PAGES = {
    "🔐 Login": login,
    "📝 Register": register,
    "🎯 Target Macros": target_macros,
    "🍽️ AI Meal Suggestions": meal_planning,
    "📊 Daily Macro Counter": macro_counter,
    "📋 My Foods List": food_list
}

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
    st.session_state["username"] = None

st.sidebar.title("📚 Navigation")

# Navigation logic
if st.session_state["user_id"]:
    selection = st.sidebar.radio("Go to", list(PAGES.keys())[2:])
    st.sidebar.success(f"👤 Logged in as {st.session_state['username']}")

    if st.sidebar.button("🚪 Logout"):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.rerun()
else:
    selection = st.sidebar.radio("Go to", ["🔐 Login", "📝 Register"])

# Load selected page
page = {
    "🔐 Login": login,
    "📝 Register": register,
    "📋 My Foods List": food_list,
    "🍽️ AI Meal Suggestions": meal_planning,
    "📊 Daily Macro Counter": macro_counter,
    "🎯 Target Macros": target_macros
}[selection]

page.show()
