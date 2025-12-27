import streamlit as st
from db import auth_sign_in, auth_sign_up, get_recipes, add_recipe, update_recipe, delete_recipe, get_photo_recipes, add_photo_recipe, upload_photo_recipe_image, delete_photo_recipe, delete_photo_recipe_image
import urllib.parse

st.set_page_config(
    page_title="Dinner Recipes",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

# st.title("🍽️ Dinner Recipe App")

def is_logged_in():
    return (
        "sb_access_token" in st.session_state
        and "sb_refresh_token" in st.session_state
    )

with st.sidebar:
    st.subheader("Account")

    if not is_logged_in():
        tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log in")

                if submitted:
                    try:
                        session = auth_sign_in(email, password)
                        st.session_state["sb_access_token"] = session["access_token"]
                        st.session_state["sb_refresh_token"] = session["refresh_token"]
                        st.success("Logged in!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")

            with tab_signup:
                with st.form("signup_form", clear_on_submit=False):
                    email2 = st.text_input("Email", key="signup_email")
                    password2 = st.text_input("Password", type="password", key="signup_password")
                    submitted2 = st.form_submit_button("Create account")

                    if submitted2:
                        try:
                            auth_sign_up(email2, password2)
                            st.success("Account created! Now go to Log in.")
                        except Exception as e:
                            st.error(f"Signup failed: {e}")

            # ⛔ STOP HERE if not logged in
            st.warning("Please log in to access the app.")
            st.stop()

    else:
        st.success("Logged in ✅")
        if st.button("Log out"):
            st.session_state.clear()
            st.rerun()

# def fetch_recipes():
#     return get_recipes(
#         st.session_state["sb_access_token"],
#         st.session_state["sb_refresh_token"],
#     )
# recipes = fetch_recipes()


# ---------- Helpers ----------
def parse_ingredients(text: str) -> list[str]:
    """
    Accepts ingredients entered either:
    - one per line
    - comma separated
    Returns a clean list of strings.
    """
    if not text:
        return []
    parts = text.replace("\n", ",").split(",")
    return [p.strip() for p in parts if p.strip()]

def flash_success(msg: str):
    st.session_state["flash_success"] = msg

def show_flash_messages():
    msg = st.session_state.pop("flash_success", None)
    if msg:
        st.success(msg)

# for sharing over email 
def build_share_email(recipe: dict) -> tuple[str, str]:
    name = recipe.get("name", "(Unnamed Recipe)")
    category = recipe.get("category", "Other")
    signature = recipe.get("signature", "Unknown")

    ing_list = recipe.get("ingredients") or []
    if isinstance(ing_list, str):
        ing_list = parse_ingredients(ing_list)

    prep_h, prep_m = minutes_to_hm(recipe.get("prep_time"))
    cook_h, cook_m = minutes_to_hm(recipe.get("cook_time"))

    subject = f"Recipe: {name}"

    body_lines = [
        f"{name}",
        "",
        f"Category: {category}",
        f"Family Signature: {signature}",
        f"Prep: {prep_h}h {prep_m}m | Cook: {cook_h}h {cook_m}m",
        "",
        "Ingredients:",
        *[f"- {i}" for i in ing_list],
        "",
        "Instructions:",
        recipe.get("instructions", ""),
        "",
        "Sent from my Dinner Recipes app 🍽️",
    ]

    body = "\n".join(body_lines)
    return subject, body

def mailto_link(to_email: str, subject: str, body: str) -> str:
    params = {
        "subject": subject,
        "body": body,
    }
    qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"mailto:{to_email}?{qs}"

def minutes_to_hm(total_minutes: int | None) -> tuple[int, int]:
    total = int(total_minutes or 0)
    return total // 60, total % 60


def safe_rerun():
    # Streamlit 1.27+ prefers st.rerun()
    try:
        st.rerun()
    except Exception:
        # If the environment doesn't support rerun for some reason,
        # the app will still continue without crashing.
        pass

show_flash_messages()
# ---------- Load Recipes (from Supabase via db.py) ----------
# recipes = get_recipes()  # each recipe should include: id, name, category, signature, ingredients(list), instructions, prep_time, cook_time, is_favorite
recipes = get_recipes(
    st.session_state["sb_access_token"],
    st.session_state["sb_refresh_token"]
)


# ---------- Sidebar ----------
menu = st.sidebar.radio("Menu", ["View Recipes", "Add Recipe", "Shopping List", "Photo Recipes", "Version Changes & Updates"])


# ---------- VIEW RECIPES ----------
if menu == "View Recipes":
    st.subheader("📖 Your Recipes")

    search = st.text_input("🔍 Search recipes")

    categories = sorted({r.get("category", "Other") for r in recipes if r.get("category")})
    selected_category = st.selectbox("Filter by Category", ["All"] + categories)

    favorites_only = st.checkbox("⭐ Favorites only")

    signatures = sorted({r.get("signature", "Unknown") for r in recipes if r.get("signature")})
    selected_signature = st.selectbox("Filter by Family Signature", ["All"] + signatures)

    # Filter list
    recipes_to_show = recipes
    if selected_signature != "All":
        recipes_to_show = [r for r in recipes_to_show if (r.get("signature") or "Unknown") == selected_signature]

    for recipe in recipes_to_show:
        name = recipe.get("name", "").strip()
        if search and search.lower() not in name.lower():
            continue
        if selected_category != "All" and recipe.get("category") != selected_category:
            continue
        if favorites_only and not bool(recipe.get("is_favorite", False)):
            continue

        recipe_id = recipe["id"]
        # exp_title = f"{'⭐ ' if recipe.get('is_favorite', False) else ''}{name or '(Unnamed Recipe)'}"
        is_macro_friendly = recipe.get("category") == "Macro Friendly"
        mf_tag = "🟢 MF " if is_macro_friendly else ""
        fav_tag = "⭐ " if recipe.get("is_favorite", False) else ""
        exp_title = f"{mf_tag}{fav_tag}{name or '(Unnamed Recipe)'}"

        with st.expander(exp_title):
            prep_h, prep_m = minutes_to_hm(recipe.get("prep_time"))
            cook_h, cook_m = minutes_to_hm(recipe.get("cook_time"))

            st.markdown(f"**Category:** {recipe.get('category', 'Other')}")
            st.markdown(f"**Family Signature:** {recipe.get('signature', 'Unknown')}")
            st.markdown(
                f"⏱️ Prep: {prep_h}h {prep_m}m  |  Cook: {cook_h}h {cook_m}m"
            )

            st.markdown("### 🧾 Ingredients")
            ing_list = recipe.get("ingredients") or []
            if isinstance(ing_list, str):
                # just in case db returns a string
                ing_list = parse_ingredients(ing_list)

            if ing_list:
                for item in ing_list:
                    st.write(f"- {item}")
            else:
                st.caption("No ingredients saved.")

            st.markdown("### 📋 Instructions")
            st.write(recipe.get("instructions", ""))

            st.divider()

            # Buttons row: Delete / Edit / Refresh
            col_del, col_edit, col_share, col_ref = st.columns(4)

            # ---------- REFRESH ----------
            # if col_ref.button("🔄 Refresh", key=f"refresh_{recipe_id}"):
            #     safe_rerun()
            # ---------- PRINT ----------
            # print_html = recipe_to_print_html(recipe)
            # col_print.download_button(
            #     "🖨️ Print",
            #     data=print_html,
            #     file_name=f"{(name or 'recipe').replace(' ', '_')}.html",
            #     mime="text/html",
            #     key=f"print_{recipe_id}",
            # )

            to_email = st.text_input("Share to email", key=f"share_to_{recipe_id}", placeholder="name@example.com")

            if col_share.button("📧 Share", key=f"share_btn_{recipe_id}"):
                if not to_email.strip():
                    st.error("Enter an email address first.")
                else:
                    subject, body = build_share_email(recipe)
                    link = mailto_link(to_email.strip(), subject, body)
                    st.markdown(f"[✅ Click here to open your email app and send]({link})")

            # ---------- DELETE ----------
            confirm_key = f"confirm_delete_{recipe_id}"
            if confirm_key not in st.session_state:
                st.session_state[confirm_key] = False

            if col_del.button("🗑️ Delete", key=f"delete_{recipe_id}"):
                st.session_state[confirm_key] = True

            if st.session_state.get(confirm_key, False):
                st.warning("⚠️ Are you sure? This cannot be undone.")
                c1, c2 = st.columns(2)
                if c1.button("❌ Cancel", key=f"cancel_delete_{recipe_id}"):
                    st.session_state[confirm_key] = False
                if c2.button("✅ Yes, Delete", key=f"yes_delete_{recipe_id}"):
                    delete_recipe(
                    st.session_state["sb_access_token"],
                    st.session_state["sb_refresh_token"],
                    recipe_id
                )
                    st.session_state[confirm_key] = False
                    st.success("Recipe deleted.")
                    safe_rerun()

            # ---------- EDIT ----------
            edit_state_key = f"editing_{recipe_id}"
            if edit_state_key not in st.session_state:
                st.session_state[edit_state_key] = False

            if col_edit.button("✏️ Edit", key=f"edit_btn_{recipe_id}"):
                st.session_state[edit_state_key] = True

            if st.session_state.get(edit_state_key, False):
                st.markdown("---")
                st.markdown("#### ✏️ Edit Recipe")

                with st.form(f"edit_form_{recipe_id}"):
                    name_in = st.text_input("Recipe Name", value=recipe.get("name", ""))
                    category_in = st.selectbox(
                        "Category",
                        ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian", "Macro Friendly","Desserts", "Other"],
                        index=["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian","Macro Friendly","Desserts", "Other"].index(
                            recipe.get("category", "Other") if recipe.get("category") in ["Chicken", "Beef", "Pasta", "Seafood","Macro Friendly","Desserts", "Vegetarian", "Other"] else "Other"
                        ),
                    )
                    signature_in = st.text_input("Family Signature", value=recipe.get("signature", "Unknown"))

                    ingredients_in = st.text_area(
                        "Ingredients (one per line or comma-separated)",
                        value="\n".join(ing_list),
                    )
                    instructions_in = st.text_area("Instructions", value=recipe.get("instructions", ""))

                    # Times (hours/minutes)
                    prep_h0, prep_m0 = minutes_to_hm(recipe.get("prep_time"))
                    cook_h0, cook_m0 = minutes_to_hm(recipe.get("cook_time"))

                    prep_hours = st.number_input("Prep Time Hours", min_value=0, value=int(prep_h0))
                    prep_minutes = st.number_input("Prep Time Minutes", min_value=0, max_value=59, value=int(prep_m0))
                    cook_hours = st.number_input("Cook Time Hours", min_value=0, value=int(cook_h0))
                    cook_minutes = st.number_input("Cook Time Minutes", min_value=0, max_value=59, value=int(cook_m0))

                    is_fav_in = st.checkbox("⭐ Mark as Favorite", value=bool(recipe.get("is_favorite", False)))

                    submitted = st.form_submit_button("Save Changes")

                if submitted:
                    updated_recipe = {
                        "name": (name_in or "").strip() or recipe.get("name", ""),
                        "category": category_in,
                        "signature": (signature_in or "").strip() or "Unknown",
                        "ingredients": parse_ingredients(ingredients_in),
                        "instructions": (instructions_in or "").strip(),
                        "prep_time": int(prep_hours) * 60 + int(prep_minutes),
                        "cook_time": int(cook_hours) * 60 + int(cook_minutes),
                        "is_favorite": bool(is_fav_in),
                    }
                    update_recipe(
                        st.session_state["sb_access_token"],
                        st.session_state["sb_refresh_token"],
                        recipe_id,
                        updated_recipe
                    )
                    st.session_state[edit_state_key] = False
                    st.success("Recipe updated.")
                    safe_rerun()


# ---------- ADD RECIPE ----------
elif menu == "Add Recipe":
    st.subheader("➕ Add a New Recipe")

    with st.form("add_recipe_form"):
        name = st.text_input("Recipe Name")
        category = st.selectbox(
            "Category",
            ["Chicken", "Beef", "Pasta", "Seafood", "Vegetarian","Macro Friendly","Desserts", "Other"],
        )
        signature = st.text_input("Family Signature (who owns this recipe)")
        ingredients_text = st.text_area("Ingredients (one per line or comma-separated)")
        instructions = st.text_area("Instructions")

        prep_hours = st.number_input("Prep Time Hours", min_value=0)
        prep_minutes = st.number_input("Prep Time Minutes", min_value=0, max_value=59)
        cook_hours = st.number_input("Cook Time Hours", min_value=0)
        cook_minutes = st.number_input("Cook Time Minutes", min_value=0, max_value=59)

        is_favorite = st.checkbox("⭐ Mark as Favorite")

        submitted = st.form_submit_button("Save Recipe")

    if submitted:
        if not name.strip():
            st.error("Recipe name is required.")
        else:
            new_recipe = {
                "name": name.strip(),
                "category": category,
                "signature": (signature or "").strip() or "Unknown",
                "ingredients": parse_ingredients(ingredients_text),
                "instructions": (instructions or "").strip(),
                "prep_time": int(prep_hours) * 60 + int(prep_minutes),
                "cook_time": int(cook_hours) * 60 + int(cook_minutes),
                "is_favorite": bool(is_favorite),
            }

            add_recipe(
                st.session_state["sb_access_token"],
                st.session_state["sb_refresh_token"],
                new_recipe
            )

            flash_success("Recipe saved! 🍲")
            st.rerun()   # or safe_rerun()



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

# ---------- NEWS & UPDATES ----------
elif menu == "Version Changes & Updates":
    st.subheader("📰 News & Version Updates")

    st.caption("What’s new in the app, bug fixes, and upcoming changes.")

    # Optional: show current version
    APP_VERSION = "v0.6.0"
    st.info(f"Current version: {APP_VERSION}")

    # Simple changelog entries (newest first)
    updates = [
        {
            "version": "v0.6.0",
            "date": "2025-12-26",
            "title": "Auth + Recipe CRUD polish",
            "changes": [
                "Improved login/logout flow",
                "Recipe edit form now supports hours/minutes for prep/cook time",
                "Delete confirmation added to prevent accidental deletes",
            ],
        },
        {
            "version": "v0.5.0",
            "date": "2025-12-20",
            "title": "Shopping List",
            "changes": [
                "Generate a shopping list from selected recipes",
                "Deduped shopping items",
            ],
        },
        {
            "version": "v0.5.0",
            "date": "2025-12-20",
            "title": "Category",
            "changes": [
                "You can now add options for desert, and macro specific categories"
                
            ],
        },
        {
            "version": "v0.5.0",
            "date": "2025-12-20",
            "title": "Added Share Functionality",
            "changes": [
                "You can now share recipes with other people natively using the Share feature.",
                "Under the recipes list there is a button for (share) and an email send to list"
                
            ],
        }
        
    ]

    for u in updates:
        with st.expander(f"{u['version']} — {u['title']} ({u['date']})", expanded=False):
            for c in u["changes"]:
                st.write(f"- {c}")

    st.divider()

    # Optional: small "roadmap" section
    st.markdown("### 🧭 Coming soon")
    st.write("- Recipe photo upload")
    st.write("- Share recipes with family members")
    st.write("- Weekly meal planner")

# ---------- RECIPE PHOTOS SECTION ----------
elif menu == "Photo Recipes":
    st.subheader("📸 Photo Recipes")
    st.caption("Upload a photo of a recipe and save it for later.")

    # --- Upload form ---
    label = st.text_input(
        "Recipe name / label",
        placeholder="e.g., Sarah's Awesome Cookies",
        key="photo_label",
    )

    uploaded = st.file_uploader(
        "Upload a recipe photo (jpg/png/webp)",
        type=["jpg", "jpeg", "png", "webp"],
        key="photo_upload",
    )

    if uploaded is not None:
        st.image(uploaded, caption="Preview", use_container_width=True)

    if st.button(" Save Photo Recipe", key="save_photo_recipe"):
        if not label.strip():
            st.error("Please enter a name/label.")
            st.stop()
        if uploaded is None:
            st.error("Please upload a photo.")
            st.stop()

        file_ext = uploaded.name.split(".")[-1].lower().replace("jpeg", "jpg")
        content_type = uploaded.type or "image/jpeg"
        file_bytes = uploaded.getvalue()

        # IMPORTANT: Make sure this uploads to your *photo* bucket
        path, url = upload_photo_recipe_image(
            st.session_state["sb_access_token"],
            st.session_state["sb_refresh_token"],
            file_bytes,
            content_type,
            file_ext,
        )

        add_photo_recipe(
            st.session_state["sb_access_token"],
            st.session_state["sb_refresh_token"],
            label.strip(),
            url, path
            # optional: store path too if your table has image_path
            # path,
        )

        st.success("Saved! ✅")
        safe_rerun()

    st.divider()

    # --- List saved photo recipes ---
    photos = get_photo_recipes(
    st.session_state["sb_access_token"],
    st.session_state["sb_refresh_token"],
    )

    if not photos:
        st.info("No photo recipes yet.")
    else:
        st.markdown("### Saved Photo Recipes")

        for p in photos:
            label_txt = str(p.get("label") or "(No label)")
            created_txt = str(p.get("created_at") or "")
            exp_label = f"🖼️ {label_txt} — {created_txt}"

            with st.expander(exp_label, expanded=False):
                st.image(p["image_url"], use_container_width=True)

                if st.button("🗑️ Delete", key=f"del_photo_{p['id']}"):
                    if p.get("image_path"):
                        delete_photo_recipe_image(
                            st.session_state["sb_access_token"],
                            st.session_state["sb_refresh_token"],
                            p["image_path"],
                        )

                    delete_photo_recipe(
                        st.session_state["sb_access_token"],
                        st.session_state["sb_refresh_token"],
                        p["id"],
                    )

                    st.success("Deleted.")
                    safe_rerun()

