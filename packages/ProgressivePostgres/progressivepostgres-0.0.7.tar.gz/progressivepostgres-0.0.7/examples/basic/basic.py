from ProgressivePostgres import Client
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

client = Client(name="TS")
# Execute a simple query, like creating a table or inserting data
client.execute_query("CREATE TABLE IF NOT EXISTS example (id SERIAL PRIMARY KEY, name TEXT);")
client.execute_query("INSERT INTO example (name) VALUES (%s)", ["test_name"])

# Query data
rows = client.execute_query("SELECT * FROM example;")
print("Rows:", rows)

# Cleanup
client.close()
