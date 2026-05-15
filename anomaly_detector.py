import pandas as pd
from datetime import timedelta

def detect_anomalies(transactions_df):
    """Flag suspicious transactions"""
    if transactions_df.empty:
        return pd.DataFrame()
    
    df = transactions_df.copy()
    
    # Initialize columns with float type (not int)
    df['anomaly_score'] = 0.0
    df['anomaly_reasons'] = ''
    df['risk_level'] = 'Low'
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Round dollar amounts over $1,000
    for idx in df.index:
        amount = df.at[idx, 'amount']
        if amount % 1 == 0 and amount > 1000:
            df.at[idx, 'anomaly_score'] = df.at[idx, 'anomaly_score'] + 0.3
            df.at[idx, 'anomaly_reasons'] = df.at[idx, 'anomaly_reasons'] + 'Round amount >$1,000; '
    
    # Weekend transactions
    if 'date' in df.columns:
        for idx in df.index:
            date_val = df.at[idx, 'date']
            if hasattr(date_val, 'dayofweek') and date_val.dayofweek >= 5:
                df.at[idx, 'anomaly_score'] = df.at[idx, 'anomaly_score'] + 0.3
                df.at[idx, 'anomaly_reasons'] = df.at[idx, 'anomaly_reasons'] + 'Weekend transaction; '
    
    # Duplicate amounts within 7 days
    if len(df) > 5:
        for idx in df.index:
            amount = df.at[idx, 'amount']
            if not isinstance(df.at[idx, 'date'], pd.Timestamp):
                continue
            
            duplicate_count = 0
            for other_idx in df.index:
                if other_idx == idx:
                    continue
                if abs(amount - df.at[other_idx, 'amount']) < 0.01:
                    duplicate_count += 1
            
            if duplicate_count >= 2:
                df.at[idx, 'anomaly_score'] = df.at[idx, 'anomaly_score'] + 0.35
                df.at[idx, 'anomaly_reasons'] = df.at[idx, 'anomaly_reasons'] + f'Duplicate amount (seen {duplicate_count + 1}x in 7 days); '
    
    # Set risk levels
    for idx in df.index:
        if df.at[idx, 'anomaly_score'] >= 0.7:
            df.at[idx, 'risk_level'] = 'High'
        elif df.at[idx, 'anomaly_score'] >= 0.3:
            df.at[idx, 'risk_level'] = 'Medium'
    
    anomalies = df[df['anomaly_score'] > 0].copy()
    return anomalies.sort_values('anomaly_score', ascending=False)