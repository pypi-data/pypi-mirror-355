import os
import argparse
from dotenv import load_dotenv
from mcp_communication import logger

load_dotenv()


def get_config():
    parser = argparse.ArgumentParser(description="MCP Communication Configuration")
    
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
    
    # Cohere configuration arguments
    parser.add_argument(
        "--cohere-api-key",
        default=None,
        help="API key for Cohere. Will use environment variable COHERE_API_KEY if not provided.",
    )

# OpenAI configuration arguments
    parser.add_argument(
        "--openai-api-key",
        default=None,
        help="API key for OpenAI. Will use environment variable OPENAI_API_KEY if not provided.",
    )

# Perplexity configuration arguments
    parser.add_argument(
        "--perplexity-api-key",
        default=None,
        help="API key for Perplexity. Will use environment variable PERPLEXITY_API_KEY if not provided.",
    )
    
    parser.add_argument(
        "--oauth-client-id",
        default=None,
        help="OAuth client ID for Perplexity. Will use environment variable OAUTH_CLIENT_ID if not provided.",
    )

    parser.add_argument(
        "--oauth-client-secret",
        default=None,
        help="OAuth client secret for Perplexity. Will use environment variable OAUTH_CLIENT_SECRET if not provided.",
    )

    parser.add_argument(
        "--gmail-auth-uri",
        default=None,
        help="Authorization URI for Gmail OAuth. Will use environment variable GMAIL_AUTH_URI if not provided.",
    )

    parser.add_argument(
        "--gmail-token-uri",
        default=None,
        help="Token URI for Gmail OAuth. Will use environment variable GMAIL_TOKEN_URI if not provided.",
    )

    parser.add_argument(
        "--gmail-redirect-uris",
        default=None,
        help="Comma-separated redirect URIs for Gmail OAuth. Will use environment variable GMAIL_REDIRECT_URIS if not provided.",
    )

    parser.add_argument(
        "--gmail-scopes",
        default=None,
        help="Comma-separated list of Gmail OAuth scopes. Will use environment variable GMAIL_SCOPES if not provided.",
    )

    parser.add_argument(
        "--whatsapp-token",
        default=None,
        help="API token for WhatsApp integration. Will use environment variable WHATSAPP_TOKEN if not provided.",
    )

    parser.add_argument(
        "--whatsapp-url",
        default=None,
        help="Base API URL for WhatsApp integration. Will use environment variable WHATSAPP_URL if not provided.",
    )
    
    args = parser.parse_args()

    # === Typesense Configuration ===
    typesense_host = args.typesense_host or os.getenv("TYPESENSE_HOST", "localhost")
    typesense_port = args.typesense_port or os.getenv("TYPESENSE_PORT", "8108")
    typesense_protocol = args.typesense_protocol or os.getenv("TYPESENSE_PROTOCOL", "http")
    typesense_api_key = args.typesense_api_key or os.getenv("TYPESENSE_API_KEY")
    
    logger.info(f"Final TYPESENSE_API_KEY: {'Set' if typesense_api_key else 'Not set'}")

    # === MongoDB Configuration ===
    mongodb_uri = args.mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db_name = args.mongodb_db_name or os.getenv("MONGODB_DB_NAME", "mcp_communication")
    
    logger.info(f"Final MONGODB_URI: {mongodb_uri[:20]}..." if mongodb_uri and len(mongodb_uri) > 20 else f"Final MONGODB_URI: {mongodb_uri}")
    logger.info(f"Final MONGODB_DB_NAME: {mongodb_db_name}")

    # === Cohere Configuration ===
    cohere_api_key = args.cohere_api_key or os.getenv("COHERE_API_KEY")
    
    logger.info(f"Final COHERE_API_KEY: {'Set' if cohere_api_key else 'Not set'}")


      # === OpenAI Configuration ===
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    logger.info(f"Final OPENAI_API_KEY: {'Set' if openai_api_key else 'Not set'}")

    # === Perplexity Configuration ===
    perplexity_api_key = args.perplexity_api_key or os.getenv("PERPLEXITY_API_KEY")
    logger.info(f"Final PERPLEXITY_API_KEY: {'Set' if perplexity_api_key else 'Not set'}")

    oauth_client_id = args.oauth_client_id or os.getenv("OAUTH_CLIENT_ID")
    logger.info(f"Final OAUTH_CLIENT_ID: {'Set' if oauth_client_id else 'Not set'}")

    oauth_client_secret = args.oauth_client_secret or os.getenv("OAUTH_CLIENT_SECRET")
    logger.info(f"Final OAUTH_CLIENT_SECRET: {'Set' if oauth_client_secret else 'Not set'}")

    gmail_auth_uri = args.gmail_auth_uri or os.getenv("GMAIL_AUTH_URI")
    logger.info(f"Final GMAIL_AUTH_URI: {'Set' if gmail_auth_uri else 'Not set'}")

    gmail_token_uri = args.gmail_token_uri or os.getenv("GMAIL_TOKEN_URI")
    logger.info(f"Final GMAIL_TOKEN_URI: {'Set' if gmail_token_uri else 'Not set'}")

    gmail_redirect_uris = args.gmail_redirect_uris or os.getenv("GMAIL_REDIRECT_URIS")
    logger.info(f"Final GMAIL_REDIRECT_URIS: {'Set' if gmail_redirect_uris else 'Not set'}")

    gmail_scopes = args.gmail_scopes or os.getenv("GMAIL_SCOPES")
    logger.info(f"Final GMAIL_SCOPES: {'Set' if gmail_scopes else 'Not set'}")

    whatsapp_token = args.whatsapp_token or os.getenv("WHATSAPP_TOKEN") 
    logger.info(f"Final WHATSAPP_TOKEN: {'Set' if whatsapp_token else 'Not set'}")

    whatsapp_url = args.whatsapp_url or os.getenv("WHATSAPP_URL")
    logger.info(f"Final WHATSAPP_URL: {'Set' if whatsapp_url else 'Not set'}")

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
        "cohere": {
            "api_key": cohere_api_key,
        },
        "openai": {
            "api_key": openai_api_key
        },
        "perplexity": {
            "api_key": perplexity_api_key
        },
        "oauth": {
            "client_id": oauth_client_id,
            "client_secret": oauth_client_secret,
            "auth_uri": gmail_auth_uri,
            "token_uri": gmail_token_uri,
            "redirect_uris": gmail_redirect_uris,
            "scopes": gmail_scopes,
        },
        "whatsapp": {
            "token": whatsapp_token,
            "url": whatsapp_url,
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

# === Cohere Configuration ===
COHERE_API_KEY = config["cohere"]["api_key"]

# Cohere validation
if not COHERE_API_KEY:
    logger.warning("Cohere API key not provided. Cohere reranking functionality will be disabled.")


# === OpenAI Configuration ===
OPENAI_API_KEY = config["openai"]["api_key"]
 
# OpenAI validation
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not provided. LLM functionality will be disabled.")

# === Perplexity Configuration ===
PERPLEXITY_API_KEY = config["perplexity"]["api_key"]
if not PERPLEXITY_API_KEY:
    logger.warning("Perplexity API key not provided. Perplexity functionality will be disabled.")

# === OAuth Configuration ===
OAUTH_CLIENT_ID = config["oauth"]["client_id"]
OAUTH_CLIENT_SECRET = config["oauth"]["client_secret"]
OAUTH_AUTH_URI = config["oauth"]["auth_uri"]
OAUTH_TOKEN_URI = config["oauth"]["token_uri"]
OAUTH_REDIRECT_URIS = config["oauth"]["redirect_uris"]
OAUTH_SCOPES = config["oauth"]["scopes"]    

# === WhatsApp Configuration ===
WHATSAPP_TOKEN = config["whatsapp"]["token"]
WHATSAPP_URL = config["whatsapp"]["url"]


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
    # Cohere
    "COHERE_API_KEY",
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    # OAuth
    "OAUTH_CLIENT_ID",
    "OAUTH_CLIENT_SECRET",
    "OAUTH_AUTH_URI",
    "OAUTH_TOKEN_URI",
    "OAUTH_REDIRECT_URIS",
    "OAUTH_SCOPES",
    # WhatsApp
    "WHATSAPP_TOKEN",
    "WHATSAPP_URL"
]

