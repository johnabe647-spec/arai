import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
import re
from supabase import create_client
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def extract_text_from_image(image_bytes):
    """Extract text from image using OCR"""
    try:
        image = Image.open(image_bytes)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"Error: {e}"

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using OCR"""
    try:
        images = convert_from_bytes(pdf_bytes)
        all_text = ""
        for image in images:
            text = pytesseract.image_to_string(image)
            all_text += text + "\n"
        return all_text
    except Exception as e:
        return f"Error: {e}"

def parse_receipt_text(text):
    """Extract structured data from receipt text"""
    
    data = {
        "merchant": "",
        "date": "",
        "total": 0.0,
        "tax": 0.0,
        "items": [],
        "confidence": "medium"
    }
    
    # Extract merchant (usually first few lines)
    lines = text.split('\n')
    for line in lines[:10]:
        if len(line) > 3 and not re.match(r'^\d', line):
            data["merchant"] = line.strip()
            break
    
    # Extract date (DD/MM/YYYY, DD-MM-YYYY, etc.)
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            data["date"] = match.group(1)
            break
    
    # Extract total amount
    total_patterns = [
        r'[Tt]otal\s*:?\s*[\$₦R]?\s*(\d+[\.,]\d{2})',
        r'[Aa]mount\s*:?\s*[\$₦R]?\s*(\d+[\.,]\d{2})',
        r'[\$₦R]\s*(\d+[\.,]\d{2})\s*$'
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text)
        if match:
            data["total"] = float(match.group(1).replace(',', ''))
            break
    
    # Extract tax (VAT)
    tax_patterns = [
        r'[Vv][Aa][Tt]\s*:?\s*[\$₦R]?\s*(\d+[\.,]\d{2})',
        r'[Tt]ax\s*:?\s*[\$₦R]?\s*(\d+[\.,]\d{2})'
    ]
    for pattern in tax_patterns:
        match = re.search(pattern, text)
        if match:
            data["tax"] = float(match.group(1).replace(',', ''))
            break
    
    # Extract line items
    item_lines = []
    for line in lines:
        if re.search(r'\d+[\.,]\d{2}', line) and len(line) < 100:
            item_lines.append(line.strip())
    data["items"] = item_lines[:10]
    
    # Determine confidence based on data completeness
    confidence_score = 0
    if data["merchant"]:
        confidence_score += 1
    if data["date"]:
        confidence_score += 1
    if data["total"] > 0:
        confidence_score += 2
    if data["tax"] > 0:
        confidence_score += 1
    
    if confidence_score >= 4:
        data["confidence"] = "high"
    elif confidence_score >= 2:
        data["confidence"] = "medium"
    else:
        data["confidence"] = "low"
    
    return data

def save_receipt(firm_id, filename, extracted_data, image_data):
    """Save receipt to database"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("receipts").insert({
            "firm_id": firm_id,
            "filename": filename,
            "merchant": extracted_data.get("merchant"),
            "receipt_date": extracted_data.get("date"),
            "total_amount": extracted_data.get("total"),
            "tax_amount": extracted_data.get("tax"),
            "items": extracted_data.get("items"),
            "confidence": extracted_data.get("confidence"),
            "raw_text": extracted_data.get("raw_text", ""),
            "processed_at": datetime.now().isoformat()
        }).execute()
        return True, result.data[0] if result.data else None
    except Exception as e:
        return False, str(e)

def get_receipts(firm_id, limit=50):
    """Get all receipts for a firm"""
    supabase = get_supabase()
    
    try:
        result = supabase.table("receipts").select("*").eq("firm_id", firm_id).order("processed_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        return []

def delete_receipt(receipt_id, firm_id):
    """Delete a receipt"""
    supabase = get_supabase()
    
    try:
        supabase.table("receipts").delete().eq("id", receipt_id).eq("firm_id", firm_id).execute()
        return True
    except Exception as e:
        return False

def create_receipts_table():
    """Create receipts table in Supabase if not exists"""
    # Run this SQL manually in Supabase
    pass

def display_receipt_ocr_interface(firm_id):
    """Display receipt OCR interface"""
    
    st.markdown("### 📸 Receipt OCR Scanner")
    st.markdown("Upload receipts to automatically extract merchant, date, amount, and tax information.")
    
    # Database table check
    st.info("ℹ️ First time using this feature? Run the SQL below in Supabase to create the receipts table.")
    
    with st.expander("📋 Click to view SQL for receipts table"):
        st.code("""
-- Create receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    firm_id INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    merchant VARCHAR(255),
    receipt_date VARCHAR(50),
    total_amount DECIMAL(10,2),
    tax_amount DECIMAL(10,2),
    items TEXT[],
    confidence VARCHAR(20),
    raw_text TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disable RLS
ALTER TABLE receipts DISABLE ROW LEVEL SECURITY;
        """, language="sql")
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Receipt (Image or PDF)",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key="receipt_upload"
    )
    
    if uploaded_file:
        st.image(uploaded_file, width=200) if uploaded_file.type.startswith('image') else None
        
        if st.button("🔍 Extract Data", type="primary"):
            with st.spinner("Processing receipt..."):
                # Extract text based on file type
                file_bytes = uploaded_file.getvalue()
                
                if uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(file_bytes)
                else:
                    text = extract_text_from_image(file_bytes)
                
                # Parse structured data
                extracted_data = parse_receipt_text(text)
                extracted_data["raw_text"] = text
                
                # Display results
                st.markdown("---")
                st.subheader("📊 Extracted Information")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Merchant:** {extracted_data['merchant'] or 'Not detected'}")
                    st.markdown(f"**Date:** {extracted_data['date'] or 'Not detected'}")
                    st.markdown(f"**Total:** ${extracted_data['total']:.2f}" if extracted_data['total'] > 0 else "**Total:** Not detected")
                
                with col2:
                    st.markdown(f"**Tax (VAT):** ${extracted_data['tax']:.2f}" if extracted_data['tax'] > 0 else "**Tax:** Not detected")
                    confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(extracted_data['confidence'], "⚪")
                    st.markdown(f"**Confidence:** {confidence_color} {extracted_data['confidence'].upper()}")
                
                if extracted_data['items']:
                    with st.expander("📋 Line Items"):
                        for item in extracted_data['items'][:10]:
                            st.write(f"- {item}")
                
                with st.expander("📄 Raw Extracted Text"):
                    st.text(text[:1000])
                
                # Save button
                if st.button("💾 Save to Database"):
                    success, result = save_receipt(
                        firm_id,
                        uploaded_file.name,
                        extracted_data,
                        file_bytes
                    )
                    if success:
                        st.success("Receipt saved successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error saving: {result}")
    
    st.markdown("---")
    
    # Show saved receipts
    st.subheader("📁 Saved Receipts")
    
    receipts = get_receipts(firm_id)
    
    if receipts:
        for receipt in receipts[:10]:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**{receipt.get('merchant', 'Unknown Merchant')}**")
                    st.caption(f"Date: {receipt.get('receipt_date', 'Unknown')}")
                    st.caption(f"File: {receipt.get('filename', 'Unknown')[:30]}")
                
                with col2:
                    st.metric("Total", f"${receipt.get('total_amount', 0):.2f}")
                    st.caption(f"Tax: ${receipt.get('tax_amount', 0):.2f}")
                
                with col3:
                    confidence = receipt.get('confidence', 'low')
                    confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
                    st.caption(f"Confidence: {confidence_icon} {confidence}")
                    
                    if st.button("Delete", key=f"del_receipt_{receipt['id']}"):
                        delete_receipt(receipt['id'], firm_id)
                        st.rerun()
                
                st.markdown("---")
        
        if len(receipts) > 10:
            st.caption(f"Showing 10 of {len(receipts)} receipts")
    else:
        st.info("No receipts saved yet. Upload a receipt to get started.")