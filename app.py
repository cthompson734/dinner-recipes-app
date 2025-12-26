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

# Ensure all recipes have a family field
for r in recipes:
    if "family" not in r:
        r["family"] = "Unknown"
save_recipes(recipes)

# ---------- Sidebar ----------
st.sidebar.subheader("Family Folder")
family_members = sorted(set(r.get("family", "Unknown") for r in recipes))
selected_family = st.sidebar.selectbox("Select Family Folder", ["All"] + family_members)

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

    # Filter recipes by family
    if selected_family != "All":
        recipes_to_show = [r for r in recipes if r.get("family") == selected_family]
    else:
        recipes_to_show = recipes

    for idx, recipe in enumerate(recipes_to_show):
        if search and search.lower() not in recipe["name"].lower():
            continue
        if selected_category != "All" and recipe["category"] != selected_category:
            continue
        if favorites_only and not recipe.get("is_favorite", False):
            continue

        with st.expander(f"{'⭐ ' if recipe.get('is_favorite', False) else ''}{recipe['name']}"):
            cols = st.columns([1, 2])
            cols[1].markdown(f"**Category:** {recipe['category']}")
            cols[1].markdown(f"**Family:** {recipe.get('family', 'Unknown')}")
            cols[1].markdown(f"⏱️ Prep: {recipe.get('prep_time', 0)} min | Cook: {recipe.get('cook_time', 0)} min")

            st.markdown("### 🧾 Ingredients")
            for item in recipe["ingredients"]:
                st.write(f"- {item}")

            st.markdown("### 📋 Instructions")
            st.write(recipe["instructions"])

        # ---------- DELETE ----------
        st.divider()
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
        edit_key = f"edit_{recipe['name']}_{idx}"  # <--- define edit_key here
        if st.button("✏️ Edit Recipe", key=edit_key):
            with st.form(f"edit_form_{recipe['name']}_{idx}"):
                name = st.text_input("Recipe Name", value=recipe['name'])
                category = st.selectbox(
                    "Category",
                    ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"],
                    index=["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"].index(recipe['category'])
                )
                family_member = st.selectbox(
                    "Family Folder",
                    ["Rhodes", "Finneran", "Thompson"],
                    index=["Rhodes", "Finneran", "Thompson"].index(recipe.get("family", "Rhodes"))
                )
                ingredients = st.text_area(
                    "Ingredients (one per line or comma-separated)",
                    value=", ".join(recipe["ingredients"])
                )
                instructions = st.text_area("Instructions", value=recipe["instructions"])
                prep_time = st.number_input("Prep Time (minutes)", min_value=0, value=recipe.get("prep_time", 0))
                cook_time = st.number_input("Cook Time (minutes)", min_value=0, value=recipe.get("cook_time", 0))
                is_favorite = st.checkbox("⭐ Mark as Favorite", value=recipe.get("is_favorite", False))

                submitted = st.form_submit_button("Save Changes")
                if submitted:
                    recipe.update({
                        "name": name,
                        "category": category,
                        "family": family_member,
                        "ingredients": [i.strip() for i in ingredients.replace("\n", ",").split(",") if i.strip()],
                        "instructions": instructions,
                        "prep_time": prep_time,
                        "cook_time": cook_time,
                        "is_favorite": is_favorite
                    })
                    save_recipes(recipes)
                    st.success("Recipe updated!")
                    st.experimental_rerun()


            # ---------- EDIT ----------
            if st.button("✏️ Edit Recipe", key=edit_key):
                with st.form(f"edit_form_{recipe['name']}_{idx}"):
                    name = st.text_input("Recipe Name", value=recipe['name'])
                    category = st.selectbox(
                        "Category",
                        ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"],
                        index=["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"].index(recipe['category'])
                    )
                    family_member = st.selectbox(
                        "Family Folder",
                        ["Rhodes", "Finneran", "Thompson"],
                        index=["Rhodes", "Finneran", "Thompson"].index(recipe.get("family", "Rhodes"))
                    )
                    ingredients = st.text_area("Ingredients (one per line or comma-separated)", 
                                               value=", ".join(recipe["ingredients"]))
                    instructions = st.text_area("Instructions", value=recipe["instructions"])
                    prep_time = st.number_input("Prep Time (minutes)", min_value=0, value=recipe.get("prep_time", 0))
                    cook_time = st.number_input("Cook Time (minutes)", min_value=0, value=recipe.get("cook_time", 0))
                    is_favorite = st.checkbox("⭐ Mark as Favorite", value=recipe.get("is_favorite", False))

                    submitted = st.form_submit_button("Save Changes")
                    if submitted:
                        recipe.update({
                            "name": name,
                            "category": category,
                            "family": family_member,
                            "ingredients": [i.strip() for i in ingredients.replace("\n", ",").split(",") if i.strip()],
                            "instructions": instructions,
                            "prep_time": prep_time,
                            "cook_time": cook_time,
                            "is_favorite": is_favorite
                        })
                        save_recipes(recipes)
                        st.success("Recipe updated!")
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
        family_member = st.selectbox(
            "Family Folder",
            ["Rhodes", "Finneran", "Thompson"]
        )
        ingredients = st.text_area("Ingredients (one per line or comma-separated)")
        instructions = st.text_area("Instructions")
        prep_time = st.number_input("Prep Time (minutes)", min_value=0)
        cook_time = st.number_input("Cook Time (minutes)", min_value=0)
        is_favorite = st.checkbox("⭐ Mark as Favorite")

        submitted = st.form_submit_button("Save Recipe")
        if submitted:
            if not name.strip():
                st.error("Recipe name is required.")
            else:
                recipes.append({
                    "name": name,
                    "category": category,
                    "family": family_member,
                    "ingredients": [i.strip() for i in ingredients.replace("\n", ",").split(",") if i.strip()],
                    "instructions": instructions,
                    "prep_time": prep_time,
                    "cook_time": cook_time,
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