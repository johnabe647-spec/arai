import pdfplumber
import pandas as pd
import re
from datetime import datetime

def parse_bank_statement(pdf_path, bank_name=None):
    """Extract transactions from PDF bank statements"""
    print(f"📄 Parsing PDF: {pdf_path}")
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception as e:
        print(f"❌ Cannot read PDF: {e}")
        return pd.DataFrame()
    
    # Auto-detect bank
    if not bank_name:
        bank_name = detect_bank(full_text)
        print(f"📍 Detected bank: {bank_name}")
    
    # Parse based on bank format
    if bank_name == "gtbank":
        transactions = parse_gtbank(full_text)
    elif bank_name == "standard_bank_za":
        transactions = parse_standard_bank_sa(full_text)
    elif bank_name == "absa_za":
        transactions = parse_absa_sa(full_text)
    elif bank_name == "kcb":
        transactions = parse_kcb(full_text)
    elif bank_name == "nmb_zim":
        transactions = parse_nmb_zimbabwe(full_text)
    else:
        transactions = parse_generic(full_text)
    
    if not transactions:
        print("⚠️ No transactions found")
        return pd.DataFrame()
    
    df = pd.DataFrame(transactions)
    print(f"✅ Found {len(df)} transactions")
    return df

def detect_bank(text):
    """Identify bank from PDF text"""
    text = text.lower()
    
    if "gtbank" in text or "guaranty trust" in text:
        return "gtbank"
    if "standard bank" in text:
        return "standard_bank_za"
    if "absa" in text:
        return "absa_za"
    if "kcb" in text or "kenya commercial bank" in text:
        return "kcb"
    if "nmb bank" in text or "nmb zimbabwe" in text:
        return "nmb_zim"
    
    return "generic"

def parse_gtbank(text):
    """GTBank Nigeria parser"""
    transactions = []
    pattern = r'(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d-%b-%Y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit'
        })
    return transactions

def parse_standard_bank_sa(text):
    """Standard Bank South Africa parser"""
    transactions = []
    pattern = r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([-]?[\d,]+\.\d{2})'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str = match
        amount = float(amount_str.replace(',', ''))
        transactions.append({
            'date': datetime.strptime(date_str, '%Y-%m-%d'),
            'description': description.strip()[:200],
            'amount': abs(amount),
            'type': 'debit' if amount < 0 else 'credit'
        })
    return transactions

def parse_absa_sa(text):
    """ABSA South Africa parser"""
    transactions = []
    lines = text.split('\n')
    
    for line in lines:
        date_match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', line)
        amount_match = re.search(r'([\d,]+\.\d{2})\s+(DR|CR)', line)
        
        if date_match and amount_match:
            date_str = date_match.group(1)
            amount = float(amount_match.group(1).replace(',', ''))
            trans_type = "debit" if amount_match.group(2) == "DR" else "credit"
            
            transactions.append({
                'date': datetime.strptime(date_str, '%d %b %Y'),
                'description': line[:200],
                'amount': amount,
                'type': trans_type
            })
    return transactions

def parse_kcb(text):
    """KCB Kenya parser"""
    transactions = []
    pattern = r'(\d{2}/\d{2}/\d{4})\s+.+?\s+(.+?)\s+([\d,]+\.\d{2})'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d/%m/%Y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit'
        })
    return transactions

def parse_nmb_zimbabwe(text):
    """NMB Zimbabwe parser"""
    transactions = []
    pattern = r'(\d{2}-[A-Za-z]{3}-\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d-%b-%y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit'
        })
    return transactions

def parse_generic(text):
    """Fallback parser for any PDF"""
    transactions = []
    lines = text.split('\n')
    
    for line in lines:
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', line)
        amount_match = re.search(r'([\d,]+\.\d{2})', line)
        
        if date_match and amount_match:
            date_str = date_match.group(1)
            amount = float(amount_match.group(1).replace(',', ''))
            
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    break
                except:
                    parsed_date = datetime.now()
            
            transactions.append({
                'date': parsed_date,
                'description': line[:200],
                'amount': abs(amount),
                'type': 'debit' if 'DR' in line.upper() else 'credit'
            })
    return transactions