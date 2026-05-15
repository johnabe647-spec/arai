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
    parsers = {
        "gtbank": parse_gtbank,
        "standard_bank_za": parse_standard_bank_sa,
        "absa_za": parse_absa_sa,
        "kcb": parse_kcb,
        "nmb_zim": parse_nmb_zimbabwe,
        "firstbank_ng": parse_firstbank_nigeria,
        "fnb_za": parse_fnb_south_africa,
        "mcb_mu": parse_mcb_mauritius,
        "coop_ke": parse_coop_kenya,
        "cbz_zim": parse_cbz_zimbabwe,
        "uba_ng": parse_uba_nigeria,
        "zenith_ng": parse_zenith_nigeria,
        "nedbank_za": parse_nedbank_sa,
        "equity_ke": parse_equity_kenya,
        "sbm_mu": parse_sbm_mauritius,
    }
    
    parser = parsers.get(bank_name, parse_generic)
    transactions = parser(full_text)
    
    if not transactions:
        print("⚠️ No transactions found")
        return pd.DataFrame()
    
    df = pd.DataFrame(transactions)
    print(f"✅ Found {len(df)} transactions")
    return df

def detect_bank(text):
    """Identify bank from PDF text (expanded)"""
    text = text.lower()
    
    # Nigerian banks
    if "gtbank" in text or "guaranty trust" in text:
        return "gtbank"
    if "first bank" in text or "firstbank" in text:
        return "firstbank_ng"
    if "uba" in text or "united bank for africa" in text:
        return "uba_ng"
    if "zenith" in text or "zenith bank" in text:
        return "zenith_ng"
    if "access bank" in text:
        return "access_ng"
    
    # South African banks
    if "standard bank" in text:
        return "standard_bank_za"
    if "absa" in text:
        return "absa_za"
    if "fnb" in text or "first national bank" in text:
        return "fnb_za"
    if "nedbank" in text:
        return "nedbank_za"
    if "capitec" in text:
        return "capitec_za"
    
    # Kenyan banks
    if "kcb" in text or "kenya commercial bank" in text:
        return "kcb"
    if "co-operative bank" in text or "coop bank" in text:
        return "coop_ke"
    if "equity bank" in text:
        return "equity_ke"
    
    # Mauritian banks
    if "mcb" in text or "mauritius commercial bank" in text:
        return "mcb_mu"
    if "sbm" in text or "state bank of mauritius" in text:
        return "sbm_mu"
    
    # Zimbabwean banks
    if "nmb bank" in text or "nmb zimbabwe" in text:
        return "nmb_zim"
    if "cbz" in text or "central bank of zimbabwe" in text:
        return "cbz_zim"
    if "steward bank" in text:
        return "steward_zim"
    
    return "generic"

# ============================================
# NEW PARSERS FOR ADDITIONAL BANKS
# ============================================

def parse_firstbank_nigeria(text):
    """First Bank Nigeria parser"""
    transactions = []
    # Pattern: 25-JAN-2025 | Description | NGN 10,000.00
    pattern = r'(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+(?:NGN|₦)?\s*([\d,]+\.\d{2})'
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

def parse_fnb_south_africa(text):
    """FNB South Africa parser"""
    transactions = []
    # Pattern: 2025/01/25 | Description | R 1,000.00
    pattern = r'(\d{4}/\d{2}/\d{2})\s+(.+?)\s+(?:R)?\s*([\d,]+\.\d{2})'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str = match
        transactions.append({
            'date': datetime.strptime(date_str, '%Y/%m/%d'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit'
        })
    return transactions

def parse_mcb_mauritius(text):
    """MCB Mauritius parser"""
    transactions = []
    # Pattern: 25/01/2025 | Description | MUR 1,000.00 | DR/CR
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+[\d,]+\s+([\d,]+\.\d{2})\s+(DR|CR)'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str, trans_type = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d/%m/%Y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit' if trans_type == 'DR' else 'credit'
        })
    return transactions

def parse_coop_kenya(text):
    """Co-operative Bank Kenya parser"""
    transactions = []
    # Pattern: 25/01/2025 | Description | KES 1,000.00
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(?:KES)?\s*([\d,]+\.\d{2})'
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

def parse_cbz_zimbabwe(text):
    """CBZ Zimbabwe parser"""
    transactions = []
    # Pattern: 25 Jan 2025 | Description | ZWL 1,000.00 | DR
    pattern = r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+(.+?)\s+[\d,]+\s+([\d,]+\.\d{2})\s+(DR|CR)'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str, trans_type = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d %b %Y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit' if trans_type == 'DR' else 'credit'
        })
    return transactions

def parse_uba_nigeria(text):
    """UBA Nigeria parser"""
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

def parse_zenith_nigeria(text):
    """Zenith Bank Nigeria parser"""
    transactions = []
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+(DR|CR)'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str, trans_type = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d/%m/%Y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit' if trans_type == 'DR' else 'credit'
        })
    return transactions

def parse_nedbank_sa(text):
    """Nedbank South Africa parser"""
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

def parse_equity_kenya(text):
    """Equity Bank Kenya parser"""
    transactions = []
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(?:KES)?\s*([\d,]+\.\d{2})'
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

def parse_sbm_mauritius(text):
    """SBM Bank Mauritius parser"""
    transactions = []
    pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+(DR|CR)'
    matches = re.findall(pattern, text)
    
    for match in matches:
        date_str, description, amount_str, trans_type = match
        transactions.append({
            'date': datetime.strptime(date_str, '%d/%m/%Y'),
            'description': description.strip()[:200],
            'amount': float(amount_str.replace(',', '')),
            'type': 'debit' if trans_type == 'DR' else 'credit'
        })
    return transactions

# ============================================
# EXISTING PARSERS (keep these)
# ============================================

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