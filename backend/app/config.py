import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://helpdesk:helpdesk@localhost:5432/helpdesk"
)
APP_VERSION = os.getenv("APP_VERSION", "dev")
ENVIRONMENT = os.getenv("APP_ENV", "local")
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false").lower() == "true"
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
