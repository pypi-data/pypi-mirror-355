import os
from dotenv import load_dotenv
import logging
import argparse
from mcp_voyage import logger

# Load environment variables from .env file if it exists
load_dotenv()

def get_config():
    parser = argparse.ArgumentParser(description="MCP Survey Configuration")
    
    # Typesense configuration arguments
    parser.add_argument(
        "--typesense-host",
        default=None,
        help="Typesense server host. Will use environment variable TYPESENSE_HOST if not provided.",
    )
    parser.add_argument(
        "--typesense-port",
        default=None,
        help="Typesense server port. Will use environment variable TYPESENSE_PORT if not provided.",
    )
    parser.add_argument(
        "--typesense-protocol",
        default=None,
        help="Typesense protocol (http/https). Will use environment variable TYPESENSE_PROTOCOL if not provided.",
    )
    parser.add_argument(
        "--typesense-api-key",
        default=None,
        help="API key for Typesense. Will use environment variable TYPESENSE_API_KEY if not provided.",
    )
    
    # MongoDB configuration arguments
    parser.add_argument(
        "--mongodb-uri",
        default=None,
        help="MongoDB connection URI. Will use environment variable MONGODB_URI if not provided.",
    )
    parser.add_argument(
        "--mongodb-db-name",
        default=None,
        help="MongoDB database name. Will use environment variable MONGODB_DB_NAME if not provided.",
    )

# OpenAI configuration arguments
    parser.add_argument(
        "--openai-api-key",
        default=None,
        help="API key for OpenAI. Will use environment variable OPENAI_API_KEY if not provided.",
    )
    
    # LlamaParse configuration arguments
    parser.add_argument(
        "--llama-api-key",
        default=None,
        help="API key for LlamaParse. Will use environment variable LLAMA_API_KEY if not provided.",
    )   

    parser.add_argument(
        "--vendor-model",
        default=None,
        help="Vendor model for LlamaParse. Will use environment variable VENDOR_MODEL if not provided.",
    )

    # NAVTOR configuration arguments
    parser.add_argument(
        "--navtor-api-base",
        default=None,
        help="API base for NAVTOR. Will use environment variable NAVTOR_API_BASE if not provided.",
    )

    parser.add_argument(
        "--navtor-username",
        default=None,
        help="Username for NAVTOR. Will use environment variable NAVTOR_USERNAME if not provided.",
    )

    parser.add_argument(
        "--navtor-password",
        default=None,
        help="Password for NAVTOR. Will use environment variable NAVTOR_PASSWORD if not provided.",
    )

    parser.add_argument(
        "--navtor-client-id",
        default=None,
        help="Client ID for NAVTOR. Will use environment variable NAVTOR_CLIENT_ID if not provided.",
    )


    parser.add_argument(
        "--navtor-client-secret",
        default=None,
        help="Client secret for NAVTOR. Will use environment variable NAVTOR_CLIENT_SECRET if not provided.",
    )

    parser.add_argument(
        "--navtor-api-key",
        default=None,
        help="API key for NAVTOR. Will use environment variable NAVTOR_API_KEY if not provided.",
    )

    # SIYA configuration arguments
    parser.add_argument(
        "--siya-api-base",
        default=None,
        help="API base for SIYA. Will use environment variable SIYA_API_BASE if not provided.",
    )

    parser.add_argument(
        "--siya-api-key",
        default=None,
        help="API key for SIYA. Will use environment variable SIYA_API_KEY if not provided.",
    )

    # Stormglass configuration arguments

    parser.add_argument(
        "--stormglass-api-base",
        default=None,
        help="API base for Stormglass. Will use environment variable STORMGLASS_API_BASE if not provided.",
    )

    parser.add_argument(
        "--stormglass-api-key",
        default=None,
        help="API key for Stormglass. Will use environment variable STORMGLASS_API_KEY if not provided.",
    )
    parser.add_argument(
        "--perplexity-api-key",
        default=None,
        help="API key for Perplexity. Will use environment variable PERPLEXITY_API_KEY if not provided.",
    )

    args, _ = parser.parse_known_args()  # ✅ this ignores unknown args like 'scheduler'
    

    # === Typesense Configuration ===
    typesense_host = args.typesense_host or os.getenv("TYPESENSE_HOST", "localhost")
    typesense_port = args.typesense_port or os.getenv("TYPESENSE_PORT", "8108")
    typesense_protocol = args.typesense_protocol or os.getenv("TYPESENSE_PROTOCOL", "http")
    typesense_api_key = args.typesense_api_key or os.getenv("TYPESENSE_API_KEY")
    
    logger.info(f"Final TYPESENSE_API_KEY: {'Set' if typesense_api_key else 'Not set'}")

    # === MongoDB Configuration ===
    mongodb_uri = args.mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db_name = args.mongodb_db_name or os.getenv("MONGODB_DB_NAME", "mcp_survey")
    
    logger.info(f"Final MONGODB_URI: {mongodb_uri[:20]}..." if mongodb_uri and len(mongodb_uri) > 20 else f"Final MONGODB_URI: {mongodb_uri}")
    logger.info(f"Final MONGODB_DB_NAME: {mongodb_db_name}")


    # === LlamaParse Configuration ===
    llama_api_key = args.llama_api_key or os.getenv("LLAMA_API_KEY")
    logger.info(f"Final LLAMA_API_KEY: {'Set' if llama_api_key else 'Not set'}")

    vendor_model = args.vendor_model or os.getenv("VENDOR_MODEL")
    logger.info(f"Final VENDOR_MODEL: {'Set' if vendor_model else 'Not set'}")

      # === OpenAI Configuration ===
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    logger.info(f"Final OPENAI_API_KEY: {'Set' if openai_api_key else 'Not set'}")

    # === NAVTOR Configuration ===
    navtor_username = args.navtor_username or os.getenv("NAVTOR_USERNAME")
    navtor_password = args.navtor_password or os.getenv("NAVTOR_PASSWORD")
    navtor_client_id = args.navtor_client_id or os.getenv("NAVTOR_CLIENT_ID")
    navtor_client_secret = args.navtor_client_secret or os.getenv("NAVTOR_CLIENT_SECRET")
    navtor_api_key = args.navtor_api_key or os.getenv("NAVTOR_API_KEY")
    navtor_api_base = args.navtor_api_base or os.getenv("NAVTOR_API_BASE")
    # === SIYA Configuration ===
    siya_api_key = args.siya_api_key or os.getenv("SIYA_API_KEY")
    siya_api_base = args.siya_api_base or os.getenv("SIYA_API_BASE")

    # === Stormglass Configuration ===
    stormglass_api_key = args.stormglass_api_key or os.getenv("STORMGLASS_API_KEY")
    stormglass_api_base = args.stormglass_api_base or os.getenv("STORMGLASS_API_BASE")

    # === Perplexity Configuration ===
    
    if args.perplexity_api_key is None:
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    else:
        perplexity_api_key = args.perplexity_api_key
    logger.info(f"Final PERPLEXITY_API_KEY: {'Set' if perplexity_api_key else 'Not set'}")

    # Return configuration for all services
    return {
        "typesense": {
            "host": typesense_host,
            "port": typesense_port,
            "protocol": typesense_protocol,
            "api_key": typesense_api_key,
        },
        "mongodb": {
            "uri": mongodb_uri,
            "db_name": mongodb_db_name,
        },

        "llama": {
            "api_key": llama_api_key,
            "vendor_model": vendor_model
        },
        "openai": {
            "api_key": openai_api_key

        },
        "navtor": {
            "username": navtor_username,
            "password": navtor_password,
            "client_id": navtor_client_id,
            "client_secret": navtor_client_secret,
            "api_key": navtor_api_key,
            "api_base": navtor_api_base
        },
        "siya": {
            "api_key": siya_api_key,
            "api_base": siya_api_base
        },
        "stormglass": {
            "api_key": stormglass_api_key,
            "api_base": stormglass_api_base

        },
        "perplexity": {
            "api_key": perplexity_api_key
        }
    }

# Get configuration values for all services
config = get_config()

# === OpenAI Configuration ===
OPENAI_API_KEY = config["openai"]["api_key"]
# === Perplexity Configuration ===
PERPLEXITY_API_KEY = config["perplexity"]["api_key"]
 
# OpenAI validation
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not provided. LLM functionality will be disabled.")
# Perplexity validation
if not PERPLEXITY_API_KEY:
    logger.warning("Perplexity API key not provided. Perplexity functionality will be disabled.")
 
# Logging configuration
LOG_DIR = os.environ.get("LOG_DIR", "logs")


# Typesense configuration
TYPESENSE_HOST = config["typesense"]["host"] or os.getenv("TYPESENSE_HOST", "localhost")
TYPESENSE_PORT = config["typesense"]["port"] or os.getenv("TYPESENSE_PORT", "8108")
TYPESENSE_PROTOCOL = config["typesense"]["protocol"] or os.getenv("TYPESENSE_PROTOCOL", "http")
TYPESENSE_API_KEY = config["typesense"]["api_key"] or os.getenv("TYPESENSE_API_KEY")

# MongoDB configuration
MONGODB_URI = config["mongodb"]["uri"] or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = config["mongodb"]["db_name"] or os.getenv("MONGODB_DB_NAME", "mcp_survey")

# NAVTOR API configuration
NAVTOR_USERNAME = config["navtor"]["username"] or os.getenv("NAVTOR_USERNAME","trial@synergyship.com")
NAVTOR_PASSWORD = config["navtor"]["password"] or os.getenv("NAVTOR_PASSWORD","fhPx8xJLz5M5Q6tz")
NAVTOR_CLIENT_ID = config["navtor"]["client_id"] or os.getenv("NAVTOR_CLIENT_ID","synergy_maritime_api_client")
NAVTOR_CLIENT_SECRET = config["navtor"]["client_secret"] or os.getenv("NAVTOR_CLIENT_SECRET","EZYdbdGXtZ3vYnQMpLKqJVwKpRrkRbXDmbE8ULbEJXXp8Fp3z6Ux6S3vhwgcDvrmtNtDHbY78adLZu5qwKmRQsdH2MV5H9KsKKZv8JupCqajmp88R7VY8PctxCnRnPny")
NAVTOR_API_KEY = config["navtor"]["api_key"] or os.getenv("NAVTOR_API_KEY","")


# SIYA API configuration
SIYA_API_KEY = config["siya"]["api_key"] or os.getenv("SIYA_API_KEY","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiNjRkMzdhMDM1Mjk5YjFlMDQxOTFmOTJhIiwiZmlyc3ROYW1lIjoiU3lpYSIsImxhc3ROYW1lIjoiRGV2IiwiZW1haWwiOiJkZXZAc3lpYS5haSIsInJvbGUiOiJhZG1pbiIsInJvbGVJZCI6IjVmNGUyODFkZDE4MjM0MzY4NDE1ZjViZiIsImlhdCI6MTc0NTY1NDg2Mn0sImlhdCI6MTc0NTY1NDg2MiwiZXhwIjoxODA4NzcwMDYyfQ.lhLfFNUnEnnjR8U0S8gMjAQrSFG_G4nhqE3-SH2dngA")

# Stormglass configuration
STORMGLASS_API_KEY = config["stormglass"]["api_key"] or os.getenv("STORMGLASS_API_KEY","72604ca2-f5ac-11ef-8c11-0242ac130003-72604d06-f5ac-11ef-8c11-0242ac130003")

# API Base URLs
STORMGLASS_API_BASE = config["stormglass"]["api_base"] or os.getenv("STORMGLASS_API_BASE","https://api.stormglass.io/v2")
NAVTOR_API_BASE = config["navtor"]["api_base"] or os.getenv("NAVTOR_API_BASE","https://api.navtor.com")
SIYA_API_BASE = config["siya"]["api_base"] or os.getenv("SIYA_API_BASE","https://dev.siya.com")

# LlamaParse configuration
LLAMA_API_KEY = config["llama"]["api_key"] or os.getenv("LLAMA_API_KEY","")
VENDOR_MODEL = config["llama"]["vendor_model"] or os.getenv("VENDOR_MODEL","")

# Stormglass parameters
STORMGLASS_DEFAULT_PARAMS = [
    "airTemperature", 
    "windSpeed", 
    "windDirection", 
    "pressure", 
    "humidity"
]

# Export values for use in other modules
__all__ = [
    # Logging
    "LOG_DIR",
    # Typesense
    "TYPESENSE_HOST",
    "TYPESENSE_PORT",
    "TYPESENSE_PROTOCOL",
    "TYPESENSE_API_KEY",

    # MongoDB
    "MONGODB_URI",
    "MONGODB_DB_NAME",
    # NAVTOR
    "NAVTOR_USERNAME",
    "NAVTOR_PASSWORD",
    "NAVTOR_CLIENT_ID",
    "NAVTOR_CLIENT_SECRET",
    "NAVTOR_API_KEY",
    # SIYA
    "SIYA_API_KEY",
    # Stormglass
    "STORMGLASS_API_KEY",
    # API URLs
    "NAVTOR_API_BASE",
    "SIYA_API_BASE",
    "STORMGLASS_API_BASE",
    # Other constants
    "STORMGLASS_DEFAULT_PARAMS",
    # LlamaParse
    "LLAMA_API_KEY",
    "VENDOR_MODEL",
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY"

]

