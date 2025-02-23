import azure.functions as func
from user_routes import (
    register_user,
    login_user,
    protected_resource,
    get_universities_endpoint,
    get_university_endpoint,
    search_universities_endpoint,
    update_calculator_config,
    get_calculator_config
)
import json
from google_auth import google_login_redirect, google_auth_callback

# We'll also import our helper from user_routes to verify session
from user_routes import verify_session
from database import get_user_by_email, _container

ALLOWED_ORIGIN = "http://localhost:5173"

def cors_preflight_response() -> func.HttpResponse:
    headers = {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Credentials": "true"
    }
    return func.HttpResponse(status_code=200, headers=headers)

def add_cors_headers(response: func.HttpResponse) -> func.HttpResponse:
    response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

app = func.FunctionApp()

@app.route(route="register", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def register_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = register_user(req)
    return add_cors_headers(response)

@app.route(route="login", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def login_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = login_user(req)
    return add_cors_headers(response)

@app.route(route="protected", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def protected_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = protected_resource(req)
    return add_cors_headers(response)

@app.route(route="stats/universities", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def stats_universities(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = get_universities_endpoint(req)
    return add_cors_headers(response)

@app.route(route="stats/university", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def stats_university(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = get_university_endpoint(req)
    return add_cors_headers(response)

@app.route(route="auth/google", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def google_login(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = google_login_redirect(req)
    return add_cors_headers(response)

@app.route(route="auth/google/callback", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def google_callback(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = google_auth_callback(req)
    return add_cors_headers(response)

@app.route(route="calculator", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def get_calculator(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = get_calculator_config(req)
    return add_cors_headers(response)

@app.route(route="calculator/update", methods=["PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def update_calculator(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = update_calculator_config(req)
    return add_cors_headers(response)

@app.route(route="universities/search", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def search_universities_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response()
    response = search_universities_endpoint(req)
    return add_cors_headers(response)


# ---------------------------------------------------------------------------
#  NEW ENDPOINT for user config wizard: /api/user/config (GET, PUT)
# ---------------------------------------------------------------------------
@app.route(route="user/config", methods=["GET", "PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def user_config_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    # Handle CORS preflight
    if req.method == "OPTIONS":
        return cors_preflight_response()

    # 1. Verify session
    is_valid, identity = verify_session(req)
    if not is_valid:
        return add_cors_headers(func.HttpResponse(
            json.dumps({"error": identity}),
            status_code=401,
            mimetype="application/json"
        ))

    # 'identity' is the user's email if valid
    user_doc = get_user_by_email(identity)
    if not user_doc:
        return add_cors_headers(func.HttpResponse(
            json.dumps({"error": "User not found."}),
            status_code=404,
            mimetype="application/json"
        ))

    # 2. GET request -> return user_doc["config"] (or empty if not set)
    if req.method == "GET":
        user_config = user_doc.get("config", {})
        resp = func.HttpResponse(json.dumps(user_config), status_code=200, mimetype="application/json")
        return add_cors_headers(resp)

    # 3. PUT request -> update user_doc["config"] with request body
    if req.method == "PUT":
        try:
            config_update = req.get_json()
        except json.JSONDecodeError:
            return add_cors_headers(func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body."}),
                status_code=400,
                mimetype="application/json"
            ))

        # If "config" doesn't exist, create an empty dict
        if "config" not in user_doc:
            user_doc["config"] = {}

        # Merge or overwrite with the new fields
        for key, value in config_update.items():
            user_doc["config"][key] = value

        # Upsert
        _container.upsert_item(user_doc)

        resp = func.HttpResponse(
            json.dumps({"message": "User config updated."}),
            status_code=200,
            mimetype="application/json"
        )
        return add_cors_headers(resp)
