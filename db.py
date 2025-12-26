import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # publishable/anon key

TABLE = "recipes"

def _client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def _authed_client(access_token: str, refresh_token: str):
    sb = _client()
    sb.auth.set_session(access_token, refresh_token)  # sets/refreshes session
    return sb

def auth_sign_in(email: str, password: str) -> dict:
    sb = _client()
    res = sb.auth.sign_in_with_password({"email": email, "password": password})
    # res.session has access_token/refresh_token
    return {"access_token": res.session.access_token, "refresh_token": res.session.refresh_token}

def auth_sign_up(email: str, password: str):
    sb = _client()
    sb.auth.sign_up({"email": email, "password": password})

def get_recipes(access_token: str, refresh_token: str):
    sb = _authed_client(access_token, refresh_token)
    res = sb.table(TABLE).select("*").order("id", desc=False).execute()
    rows = res.data or []
    for r in rows:
        r["ingredients"] = r["ingredients"].split(",") if r.get("ingredients") else []
        r["prep_time"] = int(r.get("prep_time") or 0)
        r["cook_time"] = int(r.get("cook_time") or 0)
        r["is_favorite"] = bool(r.get("is_favorite") or False)
        r["signature"] = r.get("signature") or "Unknown"
    return rows

def add_recipe(access_token: str, refresh_token: str, recipe: dict):
    sb = _authed_client(access_token, refresh_token)
    payload = recipe.copy()
    payload["ingredients"] = ",".join(payload.get("ingredients", []))
    sb.table(TABLE).insert(payload).execute()

def update_recipe(access_token: str, refresh_token: str, recipe_id: int, recipe: dict):
    sb = _authed_client(access_token, refresh_token)
    payload = recipe.copy()
    payload["ingredients"] = ",".join(payload.get("ingredients", []))
    sb.table(TABLE).update(payload).eq("id", recipe_id).execute()

def delete_recipe(access_token: str, refresh_token: str, recipe_id: int):
    sb = _authed_client(access_token, refresh_token)
    sb.table(TABLE).delete().eq("id", recipe_id).execute()



# import os
# from supabase import create_client

# SUPABASE_URL = os.environ.get("SUPABASE_URL")
# SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# if not SUPABASE_URL or not SUPABASE_KEY:
#     raise ValueError(
#         "Missing SUPABASE_URL or SUPABASE_KEY environment variables. "
#         "Set them locally (PowerShell) or in Streamlit Cloud Secrets."
#     )

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# TABLE = "recipes"


# def get_recipes():
#     res = supabase.table(TABLE).select("*").order("id", desc=False).execute()
#     rows = res.data or []
#     for r in rows:
#         r["ingredients"] = r["ingredients"].split(",") if r.get("ingredients") else []
#         r["is_favorite"] = bool(r.get("is_favorite", False))
#         r["prep_time"] = int(r.get("prep_time") or 0)
#         r["cook_time"] = int(r.get("cook_time") or 0)
#         r["signature"] = r.get("signature") or "Unknown"
#         r["category"] = r.get("category") or "Other"
#         r["name"] = r.get("name") or ""
#         r["instructions"] = r.get("instructions") or ""
#     return rows


# def add_recipe(recipe: dict):
#     payload = recipe.copy()
#     payload["ingredients"] = ",".join(payload.get("ingredients", []))
#     payload["is_favorite"] = bool(payload.get("is_favorite", False))
#     supabase.table(TABLE).insert(payload).execute()


# def update_recipe(recipe_id: int, recipe: dict):
#     payload = recipe.copy()
#     payload["ingredients"] = ",".join(payload.get("ingredients", []))
#     payload["is_favorite"] = bool(payload.get("is_favorite", False))
#     supabase.table(TABLE).update(payload).eq("id", recipe_id).execute()


# def delete_recipe(recipe_id: int):
#     supabase.table(TABLE).delete().eq("id", recipe_id).execute()


