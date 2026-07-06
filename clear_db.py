import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env variables from local .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("MONGODB_DB_NAME", "kayfa_sales_agent")

if not uri:
    print("Error: MONGODB_URI not found in .env file.")
    sys.exit(1)

print(f"Connecting to MongoDB database: {db_name} ...")
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # Trigger connection check
    client.server_info()
    
    # Drop database
    client.drop_database(db_name)
    print(f"Successfully deleted all data (dropped database '{db_name}') in MongoDB.")
except Exception as e:
    print(f"Error connecting or executing delete: {e}")
    sys.exit(1)
