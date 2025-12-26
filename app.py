import streamlit as st
import json
from pathlib import Path
from PIL import Image

DATA_FILE = Path("recipes.json")
IMAGE_DIR = Path("recipe_images")
IMAGE_DIR.mkdir(exist_ok=True)

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
st.set_page_config(
    page_title="Dinner Recipe Organizer",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Dinner Recipe App")

recipes = load_recipes()

# ---------- Sidebar ----------
menu = st.sidebar.radio(
    "Menu",
    ["View Recipes", "Add Recipe", "Shopping List"]
)

# ---------- VIEW RECIPES ----------
if menu == "View Recipes":
    st.subheader("📖 Your Recipes")

    search = st.text_input("🔍 Search recipes")

    categories = sorted(set(r["category"] for r in recipes))
    selected_category = st.selectbox(
        "Filter by Category",
        ["All"] + categories
    )

    favorites_only = st.checkbox("⭐ Favorites only")

    for recipe in recipes:
        if search and search.lower() not in recipe["name"].lower():
            continue
        if selected_category != "All" and recipe["category"] != selected_category:
            continue
        if favorites_only and not recipe["is_favorite"]:
            continue

        with st.expander(f"{'⭐ ' if recipe.get('is_favorite', False) else ''}{recipe['name']}"):
            cols = st.columns([1, 2])

            if recipe.get("image"):
                image_path = IMAGE_DIR / recipe["image"]
                if image_path.exists():
                    cols[0].image(image_path, use_container_width=True)

            cols[1].markdown(f"**Category:** {recipe['category']}")
            cols[1].markdown(
                f"⏱️ Prep: {recipe.get('prep_time', 0)} min | "
                f"Cook: {recipe.get('cook_time', 0)} min"
            )

            st.markdown("### 🧾 Ingredients")
            for item in recipe["ingredients"]:
                st.write(f"- {item}")

            st.markdown("### 📋 Instructions")
            st.write(recipe["instructions"])

            # ---------- DELETE ----------
            st.divider()

            delete_key = f"delete_{recipe['name']}"
            confirm_key = f"confirm_{recipe['name']}"

            if st.button("🗑️ Delete Recipe", key=delete_key):
                st.session_state[confirm_key] = True

            if st.session_state.get(confirm_key):
                st.warning("⚠️ Are you sure? This cannot be undone.")

                col1, col2 = st.columns(2)
                if col1.button("❌ Cancel", key=f"cancel_{recipe['name']}"):
                    st.session_state[confirm_key] = False

                if col2.button("✅ Yes, Delete", key=f"yes_{recipe['name']}"):
                    recipes.remove(recipe)
                    save_recipes(recipes)
                    st.success("Recipe deleted")
                    st.rerun()

# ---------- ADD RECIPE ----------
elif menu == "Add Recipe":
    st.subheader("➕ Add a New Recipe")

    with st.form("add_recipe_form"):
        name = st.text_input("Recipe Name")
        category = st.selectbox(
            "Category",
            ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Other"]
        )
        ingredients = st.text_area("Ingredients (one per line)")
        instructions = st.text_area("Instructions")

        prep_time = st.number_input("Prep Time (minutes)", min_value=0)
        cook_time = st.number_input("Cook Time (minutes)", min_value=0)
        is_favorite = st.checkbox("⭐ Mark as Favorite")

        image_file = st.file_uploader(
            "Recipe Image",
            type=["png", "jpg", "jpeg"]
        )

        submitted = st.form_submit_button("Save Recipe")

        if submitted:
            if not name.strip():
                st.error("Recipe name is required.")
            else:
                image_name = ""
                if image_file:
                    image_name = f"{name.replace(' ', '_').lower()}.jpg"
                    with open(IMAGE_DIR / image_name, "wb") as f:
                        f.write(image_file.getbuffer())

                recipes.append({
                    "name": name,
                    "category": category,
                    "ingredients": ingredients.splitlines(),
                    "instructions": instructions,
                    "prep_time": prep_time,
                    "cook_time": cook_time,
                    "is_favorite": is_favorite,
                    "image": image_name
                })

                save_recipes(recipes)
                st.success("Recipe saved! 🍲")

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
