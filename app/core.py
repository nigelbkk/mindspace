# core.py

from chromadb import Client

# Initialize ChromaDB client
client = Client()

# Create or get the "memories" collection
collection = client.get_or_create_collection("memories")

# Optional in-memory dict for user sessions
user_sessions = {}
