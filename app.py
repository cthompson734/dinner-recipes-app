import streamlit as st
import json
from pathlib import Path

st.set_page_config(
    page_title="Dinner Recipes",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None
    }
)

DATA_FILE = Path("recipes.json")

# ---------- Data Helpers ----------
def load_recipes():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_recipes(recipes):
    with open(DATA_FILE, "w") as f:
        json.dump(recipes, f, indent=4)

# ---------- App Setup ----------
st.title("🍽️ Dinner Recipe App")

recipes = load_recipes()

menu = st.sidebar.radio(
    "Menu",
    ["View Recipes", "Add Recipe", "Shopping List"]
)

# ---------- VIEW RECIPES ----------
if menu == "View Recipes":
    st.subheader("📖 Your Recipes")

    search = st.text_input("🔍 Search recipes")
    categories = sorted(set(r["category"] for r in recipes))
    selected_category = st.selectbox("Filter by Category", ["All"] + categories)
    favorites_only = st.checkbox("⭐ Favorites only")

    # Signature filter
    signatures = sorted(set(r.get("signature", "Unknown") for r in recipes))
    selected_signature = st.selectbox("Filter by Family Signature", ["All"] + signatures)

    recipes_to_show = recipes
    if selected_signature != "All":
        recipes_to_show = [r for r in recipes if r.get("signature") == selected_signature]

    for idx, recipe in enumerate(recipes_to_show):
        if search and search.lower() not in recipe["name"].lower():
            continue
        if selected_category != "All" and recipe["category"] != selected_category:
            continue
        if favorites_only and not recipe.get("is_favorite", False):
            continue

        with st.expander(f"{'⭐ ' if recipe.get('is_favorite', False) else ''}{recipe['name']}"):
            st.markdown(f"**Category:** {recipe['category']}")
            st.markdown(f"**Family Signature:** {recipe.get('signature', 'Unknown')}")
            st.markdown(f"⏱️ Prep: {recipe.get('prep_time', 0)} min | Cook: {recipe.get('cook_time', 0)} min")
            
            st.markdown("### 🧾 Ingredients")
            for item in recipe["ingredients"]:
                st.write(f"- {item}")
            st.markdown("### 📋 Instructions")
            st.write(recipe["instructions"])

            st.divider()

            # ---------- DELETE ----------
            delete_key = f"delete_{recipe['name']}_{idx}"
            confirm_key = f"confirm_{recipe['name']}_{idx}"
            if st.button("🗑️ Delete Recipe", key=delete_key):
                st.session_state[confirm_key] = True

            if st.session_state.get(confirm_key):
                st.warning("⚠️ Are you sure? This cannot be undone.")
                col1, col2 = st.columns(2)
                if col1.button("❌ Cancel", key=f"cancel_{recipe['name']}_{idx}"):
                    st.session_state[confirm_key] = False
                if col2.button("✅ Yes, Delete", key=f"yes_{recipe['name']}_{idx}"):
                    recipes.remove(recipe)
                    save_recipes(recipes)
                    st.success("Recipe deleted")
                    st.experimental_rerun()

            # ---------- EDIT ----------
            edit_key = f"edit_{recipe['name']}_{idx}"

            # Track editing in session_state
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False

            if st.button("✏️ Edit Recipe", key=f"edit_btn_{edit_key}"):
                st.session_state[edit_key] = True

            # Show the form if editing
            if st.session_state[edit_key]:
                with st.form(f"edit_form_{edit_key}"):
                    name = st.text_input("Recipe Name", value=recipe['name'], key=f"name_{edit_key}")
                    category = st.selectbox(
                        "Category",
                        ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"],
                        index=["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"].index(recipe['category']),
                        key=f"category_{edit_key}"
                    )
                    signature = st.text_input("Family Signature", value=recipe.get("signature", "Unknown"), key=f"signature_{edit_key}")
                    ingredients = st.text_area(
                        "Ingredients (one per line or comma-separated)",
                        value=", ".join(recipe["ingredients"]),
                        key=f"ingredients_{edit_key}"
                    )
                    instructions = st.text_area("Instructions", value=recipe["instructions"], key=f"instructions_{edit_key}")

                    # Prep Time Inputs
                    prep_hours = st.number_input("Prep Time Hours", min_value=0, value=recipe.get("prep_time",0)//60, key=f"prep_hours_{edit_key}")
                    prep_minutes = st.number_input("Prep Time Minutes", min_value=0, max_value=59, value=recipe.get("prep_time",0)%60, key=f"prep_minutes_{edit_key}")
                    prep_time_total = prep_hours * 60 + prep_minutes

                    # Cook Time Inputs
                    cook_hours = st.number_input("Cook Time Hours", min_value=0, value=recipe.get("cook_time",0)//60, key=f"cook_hours_{edit_key}")
                    cook_minutes = st.number_input("Cook Time Minutes", min_value=0, max_value=59, value=recipe.get("cook_time",0)%60, key=f"cook_minutes_{edit_key}")
                    cook_time_total = cook_hours * 60 + cook_minutes

                    is_favorite = st.checkbox("⭐ Mark as Favorite", value=recipe.get("is_favorite", False), key=f"fav_{edit_key}")

                    submitted = st.form_submit_button("Save Changes")
                    if submitted:
                        recipe.update({
                            "name": name,
                            "category": category,
                            "signature": signature.strip() or "Unknown",
                            "ingredients": [i.strip() for i in ingredients.replace("\n", ",").split(",") if i.strip()],
                            "instructions": instructions,
                            "prep_time": prep_time_total,
                            "cook_time": cook_time_total,
                            "is_favorite": is_favorite
                        })
                        save_recipes(recipes)
                        st.success("Recipe updated!")
                        st.session_state[edit_key] = False
                        st.experimental_rerun()



# ---------- ADD RECIPE ----------
elif menu == "Add Recipe":
    st.subheader("➕ Add a New Recipe")

    with st.form("add_recipe_form"):
        name = st.text_input("Recipe Name")
        category = st.selectbox(
            "Category",
            ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"]
        )
        signature = st.text_input("Family Signature (who owns this recipe)")
        ingredients = st.text_area("Ingredients (one per line or comma-separated)")
        instructions = st.text_area("Instructions")

        # Prep Time Inputs
        prep_hours = st.number_input("Prep Time Hours", min_value=0)
        prep_minutes = st.number_input("Prep Time Minutes", min_value=0, max_value=59)
        prep_time_total = prep_hours * 60 + prep_minutes

        # Cook Time Inputs
        cook_hours = st.number_input("Cook Time Hours", min_value=0)
        cook_minutes = st.number_input("Cook Time Minutes", min_value=0, max_value=59)
        cook_time_total = cook_hours * 60 + cook_minutes

        is_favorite = st.checkbox("⭐ Mark as Favorite")

        submitted = st.form_submit_button("Save Recipe")
        if submitted:
            if not name.strip():
                st.error("Recipe name is required.")
            else:
                recipes.append({
                    "name": name,
                    "category": category,
                    "signature": signature.strip() or "Unknown",
                    "ingredients": [i.strip() for i in ingredients.replace("\n", ",").split(",") if i.strip()],
                    "instructions": instructions,
                    "prep_time": prep_time_total,
                    "cook_time": cook_time_total,
                    "is_favorite": is_favorite
                })
                save_recipes(recipes)
                st.success("Recipe saved! 🍲")


# # ---------- WEEKLY PLANNER ----------
# elif menu == "Weekly Planner":
#     days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

#     st.subheader("📅 Weekly Recipe Planner")

#     # Filter recipes by selected family
#     if selected_family != "All":
#         recipes_for_planner = [r for r in recipes if r.get("family") == selected_family]
#     else:
#         recipes_for_planner = recipes

#     selected_recipes = {day: None for day in days}

#     for day in days:
#         selected_recipe = st.selectbox(f"{day}", options=["None"] + [r["name"] for r in recipes_for_planner])
#         selected_recipes[day] = selected_recipe

#     if st.button("Save Weekly Plan"):
#         plan_file = Path(f"{selected_family}_weekly_plan.json")
#         with open(plan_file, "w") as f:
#             json.dump(selected_recipes, f, indent=4)
#         st.success(f"Weekly plan saved for {selected_family}")

# ---------- SHOPPING LIST ----------
elif menu == "Shopping List":
    st.subheader("🛒 Generate Shopping List")

    selected = st.multiselect(
        "Select recipes",
        options=[r["name"] for r in recipes]
    )

    shopping_items = []
    for recipe in recipes:
        if recipe["name"] in selected:
            shopping_items.extend(recipe["ingredients"])

    if shopping_items:
        st.markdown("### 🧺 Shopping List")
        for item in sorted(set(shopping_items)):
            st.checkbox(item)