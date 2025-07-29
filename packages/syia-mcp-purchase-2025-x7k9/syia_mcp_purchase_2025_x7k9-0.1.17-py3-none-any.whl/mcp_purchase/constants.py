import os
import argparse
from dotenv import load_dotenv
from mcp_purchase import logger

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



    # Perplexity configuration arguments
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

    # === Perplexity Configuration ===
    perplexity_api_key = args.perplexity_api_key or os.getenv("PERPLEXITY_API_KEY")
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
        "perplexity": {
            "api_key": perplexity_api_key
        }
    }

# Get configuration values for all services
config = get_config()

# === Typesense Configuration ===
TYPESENSE_HOST = config["typesense"]["host"]
TYPESENSE_PORT = config["typesense"]["port"]
TYPESENSE_PROTOCOL = config["typesense"]["protocol"]
TYPESENSE_API_KEY = config["typesense"]["api_key"]

# Typesense optional validation
if not TYPESENSE_API_KEY:
    logger.warning("Typesense API key not provided. Typesense functionality will be disabled.")

# === MongoDB Configuration ===
MONGODB_URI = config["mongodb"]["uri"]
MONGODB_DB_NAME = config["mongodb"]["db_name"]

# MongoDB validation is not strict as URI could have credentials built in
if not MONGODB_URI:
    logger.warning("MongoDB URI not provided. MongoDB functionality will be disabled.")

# === LlamaParse Configuration ===
LLAMA_API_KEY = config["llama"]["api_key"]
VENDOR_MODEL = config["llama"]["vendor_model"]

if not LLAMA_API_KEY:
    logger.warning("LLAMA_API_KEY API key not provided. Document parsing functionality will be disabled.")

if not VENDOR_MODEL:
    logger.warning("VENDOR_MODEL not provided. Document parsing functionality will be disabled.")

# === OpenAI Configuration ===
OPENAI_API_KEY = config["openai"]["api_key"]

# OpenAI validation
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not provided. LLM functionality will be disabled.")

# === Perplexity Configuration ===
PERPLEXITY_API_KEY = config["perplexity"]["api_key"]
if not PERPLEXITY_API_KEY:
    logger.warning("Perplexity API key not provided. Perplexity functionality will be disabled.")

# Export values for use in other modules
__all__ = [
    # Typesense
    "TYPESENSE_HOST",
    "TYPESENSE_PORT",
    "TYPESENSE_PROTOCOL",
    "TYPESENSE_API_KEY",
    # MongoDB
    "MONGODB_URI",
    "MONGODB_DB_NAME",

    # LlamaParse
    "LLAMA_API_KEY",
    "VENDOR_MODEL",

    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY"
]