import os

# Database configuration
ENVIRONMENTS = {
    "development": "emori_dev",
    "testing": "emori_test", 
    "staging": "emori_staging",
    "production": "emori_production"
}

# Default to development if not specified
CURRENT_ENV = os.getenv("EMORI_ENV", "development")
DATABASE_NAME = ENVIRONMENTS[CURRENT_ENV]
MONGO_CONNECTION = "mongodb://host.docker.internal:27017/"

def get_database_config():
    return {
        "connection": MONGO_CONNECTION,
        "database": DATABASE_NAME,
        "environment": CURRENT_ENV
    }