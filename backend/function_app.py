import azure.functions as func
import json
import sys
import os
import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
from google_auth import google_login_redirect, google_auth_callback
from calendar_routes import get_events, create_event, update_event, delete_event
from user_profile_routes import get_user_profile, update_user_profile, get_avatar_upload_url
from account_routes import change_password, get_settings, update_settings
from module_routes import (
    get_all_modules,
    get_module,
    create_module,
    update_module,
    delete_module,
    get_modules_by_year_semester,
    get_module_suggestions
)
from dashboard_routes import (
    get_dashboard_data,
    update_dashboard_config,
    add_activity,
    update_goals,
    get_insights
)
from university_routes import (
    get_university_modules,
    get_degree_requirements,
    import_template_modules
)
from user_routes import verify_session, logout_user
from database import get_user_by_email, _container
from onboarding_routes import get_onboarding_status, save_onboarding_questionnaire
from module_routes import get_module_analytics

# Configure CORS settings - UPDATED FOR MULTIPLE ENVIRONMENTS
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,https://sarveshmina.co.uk").split(",")
DEFAULT_ORIGIN = ALLOWED_ORIGINS[0]

def is_allowed_origin(origin):
    # Check if the origin is in our allowed list, or allow all if "*" is in the list
    return "*" in ALLOWED_ORIGINS or origin in ALLOWED_ORIGINS

def cors_preflight_response(req: func.HttpRequest = None) -> func.HttpResponse:
    # Get the Origin header from the request if available
    requested_origin = req.headers.get("Origin", DEFAULT_ORIGIN) if req else DEFAULT_ORIGIN
    origin = requested_origin if is_allowed_origin(requested_origin) else DEFAULT_ORIGIN
    
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true"
    }
    return func.HttpResponse(status_code=200, headers=headers)

def add_cors_headers(response: func.HttpResponse, req: func.HttpRequest = None) -> func.HttpResponse:
    # Get the Origin header from the request if available
    requested_origin = req.headers.get("Origin", DEFAULT_ORIGIN) if req else DEFAULT_ORIGIN
    origin = requested_origin if is_allowed_origin(requested_origin) else DEFAULT_ORIGIN
    
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

app = func.FunctionApp()

@app.route(route="register", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def register_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = register_user(req)
    return add_cors_headers(response, req)

@app.route(route="login", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def login_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = login_user(req)
    return add_cors_headers(response, req)

@app.route(route="protected", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def protected_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = protected_resource(req)
    return add_cors_headers(response, req)

@app.route(route="stats/universities", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def stats_universities(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_universities_endpoint(req)
    return add_cors_headers(response, req)

@app.route(route="stats/university", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def stats_university(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_university_endpoint(req)
    return add_cors_headers(response, req)

@app.route(route="auth/google", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def google_login(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = google_login_redirect(req)
    return add_cors_headers(response, req)

@app.route(route="auth/google/callback", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def google_callback(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = google_auth_callback(req)
    return add_cors_headers(response, req)

@app.route(route="calculator", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def get_calculator(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_calculator_config(req)
    return add_cors_headers(response, req)

@app.route(route="calculator/update", methods=["PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def update_calculator(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = update_calculator_config(req)
    return add_cors_headers(response, req)

@app.route(route="universities/search", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def search_universities_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = search_universities_endpoint(req)
    return add_cors_headers(response, req)

@app.route(route="user/config", methods=["GET", "PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def user_config_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    # Handle CORS preflight
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    # 1. Verify session
    is_valid, identity = verify_session(req)
    if not is_valid:
        response = func.HttpResponse(
            json.dumps({"error": identity}),
            status_code=401,
            mimetype="application/json"
        )
        return add_cors_headers(response, req)

    # 'identity' is the user's email if valid
    user_doc = get_user_by_email(identity)
    if not user_doc:
        response = func.HttpResponse(
            json.dumps({"error": "User not found."}),
            status_code=404,
            mimetype="application/json"
        )
        return add_cors_headers(response, req)

    # 2. GET request -> return user_doc["config"] (or empty if not set)
    if req.method == "GET":
        user_config = user_doc.get("config", {})
        response = func.HttpResponse(
            json.dumps(user_config),
            status_code=200,
            mimetype="application/json"
        )
        return add_cors_headers(response, req)

    if req.method == "PUT":
        config_update = req.get_json()
        if "config" not in user_doc:
            user_doc["config"] = {}

        # Merge or overwrite fields
        for key, value in config_update.items():
            user_doc["config"][key] = value

        _container.upsert_item(user_doc)

        response = func.HttpResponse(
            json.dumps({"message": "User config updated."}),
            status_code=200,
            mimetype="application/json"
        )
        return add_cors_headers(response, req)

@app.route(route="calendar/events", methods=["GET", "POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def calendar_events(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "GET":
        response = get_events(req)
    elif req.method == "POST":
        response = create_event(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="calendar/events/{id}", methods=["PUT", "DELETE", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def calendar_event_by_id(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "PUT":
        response = update_event(req)
    elif req.method == "DELETE":
        response = delete_event(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="user/profile", methods=["GET", "PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def user_profile(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "GET":
        response = get_user_profile(req)
    elif req.method == "PUT":
        response = update_user_profile(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="user/avatar-upload", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def avatar_upload(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_avatar_upload_url(req)
    return add_cors_headers(response, req)

@app.route(route="user/password", methods=["PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def password_change(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = change_password(req)
    return add_cors_headers(response, req)

@app.route(route="user/settings", methods=["GET", "PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def settings_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "GET":
        response = get_settings(req)
    elif req.method == "PUT":
        response = update_settings(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="modules", methods=["GET", "POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def modules_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "GET":
        response = get_all_modules(req)
    elif req.method == "POST":
        response = create_module(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="modules/{id}", methods=["GET", "PUT", "DELETE", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def module_by_id_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "GET":
        response = get_module(req)
    elif req.method == "PUT":
        response = update_module(req)
    elif req.method == "DELETE":
        response = delete_module(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="dashboard", methods=["GET", "PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def dashboard_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "GET":
        response = get_dashboard_data(req)
    elif req.method == "PUT":
        response = update_dashboard_config(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="dashboard/activity", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def activity_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "POST":
        response = add_activity(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

@app.route(route="dashboard/goals", methods=["PUT", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def goals_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)

    if req.method == "PUT":
        response = update_goals(req)
    else:
        response = func.HttpResponse(
            json.dumps({"error": f"Method {req.method} not allowed"}),
            status_code=405,
            mimetype="application/json"
        )

    return add_cors_headers(response, req)

# New routes for enhanced module features

@app.route(route="modules/by-year-semester", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def modules_by_year_semester_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_modules_by_year_semester(req)
    return add_cors_headers(response, req)

@app.route(route="modules/suggestions", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def module_suggestions_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_module_suggestions(req)
    return add_cors_headers(response, req)

# New routes for university-specific features

@app.route(route="university/modules", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def university_modules_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_university_modules(req)
    return add_cors_headers(response, req)

@app.route(route="university/degree-requirements", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def degree_requirements_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_degree_requirements(req)
    return add_cors_headers(response, req)

@app.route(route="university/import-modules", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def import_modules_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = import_template_modules(req)
    return add_cors_headers(response, req)

# New dashboard insights route

@app.route(route="dashboard/insights", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def insights_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_insights(req)
    return add_cors_headers(response, req)


@app.route(route="onboarding/status", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def onboarding_status_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_onboarding_status(req)
    return add_cors_headers(response, req)

@app.route(route="onboarding/save", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def save_onboarding_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = save_onboarding_questionnaire(req)
    return add_cors_headers(response, req)


@app.route(route="modules/analytics", methods=["GET", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def module_analytics_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = get_module_analytics(req)
    return add_cors_headers(response, req)

@app.route(route="logout", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def logout_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return cors_preflight_response(req)
    response = logout_user(req)
    return add_cors_headers(response, req)