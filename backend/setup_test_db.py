import os
import re
import sys
from urllib.parse import urlparse, parse_qs, urlunparse

import psycopg
from psycopg.errors import DuplicateDatabase

# Load DATABASE_URL from .env file
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        print(f".env file not found at {env_path}")
        return {}
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

env_vars = load_env()
DATABASE_URL = env_vars.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    sys.exit(1)

# Parse the URL
parsed = urlparse(DATABASE_URL)
# We'll connect to the default database to create a new one
# Change the path to '/postgres' to connect to the default database
# Note: the original URL might have a database name in the path
# We'll replace the database name with 'postgres'
# But first, let's get the components
username = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port or 5432
# The query string
query = parse_qs(parsed.query)
# We'll keep the query parameters as they are, but we might need to adjust for the new database
# We'll remove the database name from the path and set it to 'postgres'
# Then we'll create a new database with a test name

# Connect to the server to create a new database
# We'll connect to the 'postgres' database on the same server
# Construct a URL for the postgres database
postgres_url = urlunparse((
    parsed.scheme,
    f"{host}:{port}" if port else host,
    "postgres",
    parsed.params,
    parsed.query,
    parsed.fragment
))

# Remove the query parameters that are specific to the original database? We'll keep them.
# But note: the original DATABASE_URL might have sslmode and channel_binding.
# We'll keep them.

print(f"Connecting to server to create test database: {postgres_url}")

try:
    with psycopg.connect(postgres_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            # Check if the test database already exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("sahyak_test_db",))
            exists = cur.fetchone()
            if exists:
                print("Test database already exists, using it.")
            else:
                cur.execute("CREATE DATABASE sahayak_test_db")
                print("Test database created successfully.")
except Exception as e:
    print(f"Failed to create or access test database: {e}")
    sys.exit(1)

# Now construct the TEST_DATABASE_URL
# We'll use the same host, port, user, password, but change the database name to sahayak_test_db
# And keep the same query parameters
test_parsed = list(parsed)
test_parsed[2] = "/sahyak_test_db"  # change the path
TEST_DATABASE_URL = urlunparse(test_parsed)

print(f"TEST_DATABASE_URL={TEST_DATABASE_URL}")

# Set the environment variable for the tests
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL

# Now run the integration tests
print("Running integration tests...")
result = os.system("cd /Users/bishalchaudhary/Sahayak/backend && python3 -m pytest tests/integration/test_phase5_conversation.py -v")
if result != 0:
    print("Integration tests failed.")
else:
    print("Integration tests passed.")

# We do not drop the test database to avoid destruction.
# The test database will be left for inspection or manual cleanup.
print("Test database sahayak_test_db left intact.")

sys.exit(result)