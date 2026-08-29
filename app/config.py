import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
ALLOWED_ORIGINS = [
    origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",") if origin.strip()
]
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
WIDGET_JS_VERSION = os.environ.get("WIDGET_JS_VERSION", "1")