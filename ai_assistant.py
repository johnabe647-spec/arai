import streamlit as st
from openai import OpenAI
import pandas as pd
import json

def get_openai_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def analyze_audit_with_ai(audit_data, user_query):
    """Process natural language queries about audit data"""
    client = get_openai_client()
    
    # Prepare context from audit data
    context = f"""
    Audit Summary:
    - Match Rate: {audit_data.get('match_rate', 0):.1%}
    - Matched Transactions: {audit_data.get('matched', 0)}
    - Unmatched Bank: {audit_data.get('unmatched_bank', 0)}
    - Unmatched Ledger: {audit_data.get('unmatched_ledger', 0)}
    - Anomalies Found: {audit_data.get('anomalies', 0)}
    - Fraud Risk: {audit_data.get('fraud_risk', 0):.0f}%
    - Problem Areas: {', '.join(audit_data.get('problem_areas', {}).keys())}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI audit assistant. Help auditors understand their audit data."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {user_query}"}
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def generate_audit_summary(audit_data):
    """Generate a natural language summary of the audit"""
    client = get_openai_client()
    
    context = f"""
    Match Rate: {audit_data.get('match_rate', 0):.1%}
    Fraud Risk: {audit_data.get('fraud_risk', 0):.0f}%
    Anomalies: {audit_data.get('anomalies', 0)}
    Problem Areas: {', '.join(audit_data.get('problem_areas', {}).keys())}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI audit assistant. Provide a concise executive summary."},
            {"role": "user", "content": f"Summarize this audit in 2-3 sentences for a manager: {context}"}
        ],
        temperature=0.5,
        max_tokens=200
    )
    
    return response.choices[0].message.content