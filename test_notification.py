from supabase import create_client
import streamlit as st

# Your Supabase credentials
SUPABASE_URL = "your-url-here"
SUPABASE_KEY = "your-key-here"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Try to insert a test notification (replace 3 with your actual firm_id)
result = supabase.table("notifications").insert({
    "firm_id": 3,
    "title": "Test Notification",
    "message": "This is a test",
    "type": "info",
    "is_read": False
}).execute()

print(f"Insert result: {result.data}")

# Now query it
query = supabase.table("notifications").select("*").eq("firm_id", 3).execute()
print(f"Query result: {query.data}")