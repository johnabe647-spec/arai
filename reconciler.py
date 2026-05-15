import pandas as pd
from rapidfuzz import fuzz
from datetime import timedelta

def reconcile(bank_df, ledger_df):
    """
    Match bank transactions against ledger entries.
    Returns matched, unmatched, and summary.
    """
    # Make copies to avoid modifying originals
    bank_df = bank_df.copy()
    ledger_df = ledger_df.copy()
    
    # Standardize dates
    bank_df['date'] = pd.to_datetime(bank_df['date'])
    ledger_df['date'] = pd.to_datetime(ledger_df['date'])
    
    # Add matching status columns
    bank_df['matched'] = False
    bank_df['match_score'] = 0.0
    bank_df['matched_description'] = ''
    
    ledger_df['matched'] = False
    
    matched_list = []
    unmatched_bank_list = []
    
    # For each bank transaction, find best matching ledger entry
    for bank_idx, bank_row in bank_df.iterrows():
        best_match = None
        best_score = 0
        
        # Only look at ledger entries within 3 days
        possible_matches = ledger_df[
            (ledger_df['date'] >= bank_row['date'] - timedelta(days=3)) &
            (ledger_df['date'] <= bank_row['date'] + timedelta(days=3)) &
            (ledger_df['matched'] == False)
        ]
        
        if possible_matches.empty:
            unmatched_bank_list.append(bank_row)
            continue
        
        # Score each possible match
        for ledger_idx, ledger_row in possible_matches.iterrows():
            # Amounts must match within 1 cent
            if abs(bank_row['amount'] - abs(ledger_row['amount'])) > 0.01:
                continue
            
            # Compare descriptions using fuzzy matching
            desc_score = fuzz.ratio(
                str(bank_row.get('description', '')),
                str(ledger_row.get('description', ''))
            ) / 100.0
            
            if desc_score > best_score and desc_score > 0.4:
                best_score = desc_score
                best_match = (ledger_idx, ledger_row)
        
        if best_match:
            ledger_idx, ledger_row = best_match
            
            bank_df.at[bank_idx, 'matched'] = True
            bank_df.at[bank_idx, 'match_score'] = best_score
            bank_df.at[bank_idx, 'matched_description'] = ledger_row.get('description', '')
            
            ledger_df.at[ledger_idx, 'matched'] = True
            
            matched_list.append({
                'bank_date': bank_row['date'],
                'bank_amount': bank_row['amount'],
                'bank_description': bank_row.get('description', ''),
                'ledger_date': ledger_row['date'],
                'ledger_amount': ledger_row['amount'],
                'ledger_description': ledger_row.get('description', ''),
                'match_confidence': f"{best_score*100:.0f}%"
            })
        else:
            unmatched_bank_list.append(bank_row)
    
    unmatched_ledger_list = ledger_df[ledger_df['matched'] == False]
    
    return {
        'matched': pd.DataFrame(matched_list) if matched_list else pd.DataFrame(),
        'unmatched_bank': pd.DataFrame(unmatched_bank_list) if unmatched_bank_list else pd.DataFrame(),
        'unmatched_ledger': unmatched_ledger_list,
        'summary': {
            'total_bank': len(bank_df),
            'total_ledger': len(ledger_df),
            'matched': len(matched_list),
            'unmatched_bank': len(unmatched_bank_list),
            'unmatched_ledger': len(unmatched_ledger_list),
            'match_rate': len(matched_list) / len(bank_df) if len(bank_df) > 0 else 0
        }
    }