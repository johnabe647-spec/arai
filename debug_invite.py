from supabase import create_client
import secrets
import string
from datetime import datetime, timedelta

# Paste your Supabase credentials here (from .streamlit/secrets.toml)
SUPABASE_URL = "https://lfsmvtmuuetysuddlqrq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxmc212dG11dWV0eXN1ZGRscXJxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg4Njk5OTgsImV4cCI6MjA5NDQ0NTk5OH0.ofj3sU9sZX1PbyD94NVdDy4ePqnnA_UtJh-JxWSYfis"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_invite_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

# Your firm ID
FIRM_ID = 2
EMAIL = "test@example.com"
ROLE = "staff"

print("=" * 50)
print("DEBUGGING TEAM INVITES")
print("=" * 50)

# Step 1: Check if firms table exists and find your firm
print("\n1. Checking firms table...")
try:
    firms = supabase.table("firms").select("*").execute()
    print(f"   ✅ Firms table accessible. Found {len(firms.data)} firms.")
    for firm in firms.data:
        print(f"   - ID={firm['id']}, Name={firm['name']}")
    
    # Check if firm_id 2 exists
    firm_exists = any(firm['id'] == FIRM_ID for firm in firms.data)
    if firm_exists:
        print(f"   ✅ Firm ID {FIRM_ID} exists!")
    else:
        print(f"   ❌ Firm ID {FIRM_ID} does NOT exist!")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 2: Check if team_invites table exists
print("\n2. Checking team_invites table...")
try:
    test = supabase.table("team_invites").select("*").limit(1).execute()
    print(f"   ✅ team_invites table accessible.")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 3: Check users table for role column
print("\n3. Checking users table...")
try:
    users = supabase.table("users").select("*").limit(1).execute()
    if users.data:
        print(f"   ✅ Users table accessible.")
        print(f"   Columns in users: {list(users.data[0].keys())}")
        if 'role' in users.data[0]:
            print(f"   ✅ 'role' column exists in users")
        else:
            print(f"   ❌ 'role' column MISSING from users")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 4: Try to insert an invite
print("\n4. Attempting to insert invite...")
token = generate_invite_token()
expires_at = datetime.now() + timedelta(days=7)

print(f"   Inserting with:")
print(f"   - firm_id: {FIRM_ID}")
print(f"   - email: {EMAIL}")
print(f"   - role: {ROLE}")
print(f"   - token: {token}")
print(f"   - expires_at: {expires_at.isoformat()}")

try:
    result = supabase.table("team_invites").insert({
        "firm_id": FIRM_ID,
        "email": EMAIL,
        "role": ROLE,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "used": False
    }).execute()
    
    print(f"\n   ✅ SUCCESS!")
    print(f"   Invite created with token: {token}")
    print(f"   Invite link: https://johnabe647-spec-arai.streamlit.app?invite={token}")
    print(f"   Full result: {result.data}")
    
except Exception as e:
    print(f"\n   ❌ FAILED!")
    print(f"   Error: {e}")
    print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 50)
print("DEBUG COMPLETE")
print("=" * 50)