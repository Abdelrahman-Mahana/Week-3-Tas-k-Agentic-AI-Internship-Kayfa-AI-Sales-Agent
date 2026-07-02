"""
MongoDB client and collection accessors.
Shared by all parts of the app (agent, monitoring, auth).
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from core.config import get_settings

_settings = get_settings()

# Singleton MongoDB client
_client: MongoClient | None = None
_db: Database | None = None


def get_mongo_client() -> MongoClient:
    """Return (or create) the shared MongoDB client."""
    global _client
    if _client is None:
        _client = MongoClient(
            _settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
        )
    return _client


def get_db() -> Database:
    """Return the application database."""
    global _db
    if _db is None:
        _db = get_mongo_client()[_settings.MONGODB_DB_NAME]
    return _db


# ---------------------------------------------------------------------------
# Collection getters — used by pages and agent modules
# ---------------------------------------------------------------------------

def get_users_collection() -> Collection:
    """Users collection for authentication."""
    return get_db()["users"]


def get_leads_collection() -> Collection:
    """Leads / CRM tickets created by the sales agent."""
    return get_db()["leads"]


def get_usage_logs_collection() -> Collection:
    """Usage logs for cost monitoring (Part 2.A)."""
    return get_db()["usage_logs"]


def get_behaviour_logs_collection() -> Collection:
    """Behaviour / decision trace logs (Part 2.B)."""
    return get_db()["behaviour_logs"]


def get_kb_chunks_collection() -> Collection:
    """Optional: store chunked knowledge base metadata for inspection."""
    return get_db()["kb_chunks"]


def close_connection():
    """Close the MongoDB client (useful for tests and graceful shutdown)."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
