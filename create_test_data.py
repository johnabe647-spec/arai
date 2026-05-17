import pandas as pd
from datetime import datetime, timedelta
import random

def generate_test_data():
    """Generate synthetic bank and ledger data for testing"""
    
    print("📊 Generating sample test data...")
    
    start_date = datetime(2025, 1, 1)
    
    # Create 30 sample bank transactions
    bank_transactions = []
    
    descriptions = [
        "Salary payment",
        "Office supplies - Stationery",
        "Client payment - Invoice #1234",
        "Bank charges - Monthly fee",
        "ATM withdrawal - Main branch",
        "Transfer to supplier - ABC Ltd",
        "Internet subscription - Monthly",
        "Rent payment - Office",
        "Consulting fee - Client XYZ",
        "Software license - Monthly",
        "Travel reimbursement",
        "Tax payment - VAT",
        "Dividend received",
        "Interest earned",
        "Insurance premium"
    ]
    
    for i in range(30):
        date = start_date + timedelta(days=random.randint(0, 40))
        amount = round(random.uniform(10, 5000), 2)
        
        # Add some round dollar amounts for anomaly detection
        if random.random() < 0.1:
            amount = float(int(amount))
        
        trans_type = random.choice(['credit', 'debit'])
        
        bank_transactions.append({
            'date': date,
            'amount': amount if trans_type == 'credit' else -amount,
            'description': random.choice(descriptions),
            'type': trans_type
        })
    
    bank_df = pd.DataFrame(bank_transactions)
    
    # Create ledger (similar to bank but with differences)
    ledger_transactions = bank_df.copy()
    ledger_transactions['amount'] = ledger_transactions['amount'].abs()
    
    # Add 5 extra ledger entries (unmatched in bank)
    for i in range(5):
        ledger_transactions.loc[len(ledger_transactions)] = {
            'date': start_date + timedelta(days=random.randint(0, 40)),
            'amount': round(random.uniform(50, 500), 2),
            'description': 'Internal adjustment - No bank record',
            'type': 'debit'
        }
    
    # Remove 3 bank entries (unmatched in ledger)
    bank_df = bank_df.drop(random.sample(range(len(bank_df)), 3))
    
    # Add a suspicious transaction (high risk anomaly)
    bank_df.loc[len(bank_df)] = {
        'date': datetime(2025, 1, 15),
        'amount': 5000.00,
        'description': 'Suspicious round amount payment',
        'type': 'debit'
    }
    
    # Add duplicate transactions for anomaly detection
    dup_amount = round(random.uniform(100, 500), 2)
    for i in range(3):
        bank_df.loc[len(bank_df)] = {
            'date': start_date + timedelta(days=random.randint(5, 10)),
            'amount': dup_amount,
            'description': f'Duplicate payment #{i+1}',
            'type': 'debit'
        }
    
    # Save to Excel files
    bank_df.to_excel('test_bank.xlsx', index=False)
    ledger_transactions.to_excel('test_ledger.xlsx', index=False)
    
    print(f"✅ Created test_bank.xlsx ({len(bank_df)} transactions)")
    print(f"✅ Created test_ledger.xlsx ({len(ledger_transactions)} entries)")
    print("\n📝 To test the system, run:")
    print("   streamlit run app.py")
    print("   Then upload test_bank.xlsx and test_ledger.xlsx")

if __name__ == "__main__":
    generate_test_data()