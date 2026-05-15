import pandas as pd
from datetime import datetime, timedelta
import random

# Create bank transactions
bank_data = []
for i in range(20):
    date = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 30))
    amount = round(random.uniform(10, 5000), 2)
    bank_data.append({
        'date': date,
        'amount': amount,
        'description': f'Transaction {i+1}'
    })

bank_df = pd.DataFrame(bank_data)
bank_df.to_excel('test_bank.xlsx', index=False)

# Create ledger (slightly different for testing)
ledger_data = bank_data.copy()
# Remove 2 transactions to test unmatched
ledger_data = ledger_data[:-2]
ledger_df = pd.DataFrame(ledger_data)
ledger_df.to_excel('test_ledger.xlsx', index=False)

print("✅ Created test_bank.xlsx and test_ledger.xlsx")