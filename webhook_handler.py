from flask import Flask, request, jsonify
import hmac
import hashlib
import json
from supabase import create_client
import os

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_signature(payload, signature):
    """Verify webhook signature"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Signature')
    
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    event = request.json
    
    if event['meta']['event_name'] == 'order_created':
        # New subscription created
        data = event['data']['attributes']
        custom_data = data.get('custom', {})
        firm_id = custom_data.get('firm_id')
        
        if firm_id:
            # Determine plan from variant
            variant_id = data['first_order_item']['variant_id']
            
            if variant_id == os.environ.get("PROFESSIONAL_VARIANT_ID"):
                tier = "professional"
            else:
                tier = "enterprise"
            
            supabase.table("firms").update({
                "subscription_tier": tier,
                "subscription_status": "active",
                "lemonsqueezy_customer_id": data['customer_id']
            }).eq("id", int(firm_id)).execute()
    
    elif event['meta']['event_name'] == 'subscription_updated':
        # Subscription status changed
        data = event['data']['attributes']
        # Handle status updates
    
    elif event['meta']['event_name'] == 'subscription_cancelled':
        # Subscription cancelled
        data = event['data']['attributes']
        # Handle cancellation
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(port=5000)