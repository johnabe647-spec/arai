import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

class AuditPredictor:
    """Predict fraud probability, audit time, and problem areas"""
    
    def __init__(self):
        self.fraud_model = None
        self.time_model = None
        self.scaler = None
        self.is_trained = False
        
    def extract_features(self, df):
        """Extract features from transaction data for predictions"""
        if df.empty:
            return None
        
        features = {}
        
        # Basic counts
        features['transaction_count'] = len(df)
        features['total_amount'] = df['amount'].sum()
        features['avg_amount'] = df['amount'].mean()
        features['std_amount'] = df['amount'].std() if len(df) > 1 else 0
        
        # Round dollar transactions (potential fraud indicator)
        round_dollars = df[df['amount'] % 1 == 0]
        features['round_dollar_count'] = len(round_dollars)
        features['round_dollar_pct'] = len(round_dollars) / len(df) if len(df) > 0 else 0
        
        # Large transactions (>$1000)
        large_transactions = df[df['amount'] > 1000]
        features['large_transaction_count'] = len(large_transactions)
        features['large_transaction_pct'] = len(large_transactions) / len(df) if len(df) > 0 else 0
        
        # Duplicate amounts
        duplicate_count = 0
        for amount in df['amount']:
            if len(df[df['amount'] == amount]) > 1:
                duplicate_count += 1
        features['duplicate_pct'] = duplicate_count / len(df) if len(df) > 0 else 0
        
        # Weekend transactions (if date column exists)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            weekend_count = df[df['date'].dt.dayofweek >= 5].shape[0]
            features['weekend_pct'] = weekend_count / len(df) if len(df) > 0 else 0
        else:
            features['weekend_pct'] = 0
        
        # Debit/credit ratio (if type column exists)
        if 'type' in df.columns:
            debit_count = df[df['type'] == 'debit'].shape[0]
            features['debit_ratio'] = debit_count / len(df) if len(df) > 0 else 0.5
        else:
            features['debit_ratio'] = 0.5
        
        return features
    
    def train_fraud_model(self, historical_data, labels):
        """
        Train fraud prediction model
        historical_data: list of transaction DataFrames
        labels: list of 0/1 (fraud present or not)
        """
        print("🔄 Training fraud prediction model...")
        
        # Extract features from each audit
        feature_list = []
        for df in historical_data:
            features = self.extract_features(df)
            if features:
                feature_list.append(features)
        
        if not feature_list:
            print("⚠️ No valid training data")
            return False
        
        # Create feature matrix
        X = pd.DataFrame(feature_list)
        y = np.array(labels)
        
        # Handle missing values
        X = X.fillna(0)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest Classifier
        self.fraud_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.fraud_model.fit(X_scaled, y)
        
        # Calculate accuracy
        score = self.fraud_model.score(X_scaled, y)
        print(f"✅ Fraud model trained (accuracy: {score:.2%})")
        
        self.is_trained = True
        return True
    
    def train_time_model(self, historical_data, actual_hours):
        """
        Train time prediction model
        historical_data: list of transaction DataFrames
        actual_hours: list of actual hours spent
        """
        print("🔄 Training time prediction model...")
        
        # Extract features from each audit
        feature_list = []
        for df in historical_data:
            features = self.extract_features(df)
            if features:
                feature_list.append(features)
        
        if not feature_list:
            print("⚠️ No valid training data")
            return False
        
        # Create feature matrix
        X = pd.DataFrame(feature_list)
        y = np.array(actual_hours)
        
        # Handle missing values
        X = X.fillna(0)
        
        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        # Train Random Forest Regressor
        self.time_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.time_model.fit(X_scaled, y)
        
        # Calculate R² score
        score = self.time_model.score(X_scaled, y)
        print(f"✅ Time model trained (R²: {score:.2%})")
        
        return True
    
    def predict_fraud_risk(self, df):
        """Predict fraud probability for a single audit (0-100%)"""
        if self.fraud_model is None:
            # Return heuristic-based score if model not trained
            return self._heuristic_fraud_score(df)
        
        features = self.extract_features(df)
        if not features:
            return 0
        
        X = pd.DataFrame([features]).fillna(0)
        X_scaled = self.scaler.transform(X)
        
        probability = self.fraud_model.predict_proba(X_scaled)[0][1]
        return probability * 100
    
    def _heuristic_fraud_score(self, df):
        """Fallback fraud score using simple rules"""
        if df.empty:
            return 0
        
        score = 0
        
        # Round dollar penalty
        round_count = len(df[df['amount'] % 1 == 0])
        score += min(30, round_count * 5)
        
        # Large transaction penalty
        large_count = len(df[df['amount'] > 5000])
        score += min(30, large_count * 10)
        
        # Duplicate penalty
        duplicate_count = 0
        for amount in df['amount']:
            if len(df[df['amount'] == amount]) > 1:
                duplicate_count += 1
        score += min(20, duplicate_count * 2)
        
        # Weekend penalty
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            weekend_count = df[df['date'].dt.dayofweek >= 5].shape[0]
            score += min(20, weekend_count * 5)
        
        return min(100, score)
    
    def predict_audit_time(self, df):
        """Predict audit time in hours"""
        if self.time_model is None:
            # Return heuristic-based time if model not trained
            return self._heuristic_time_prediction(df)
        
        features = self.extract_features(df)
        if not features:
            return 0
        
        X = pd.DataFrame([features]).fillna(0)
        X_scaled = self.scaler.transform(X)
        
        hours = self.time_model.predict(X_scaled)[0]
        return max(1, round(hours, 1))
    
    def _heuristic_time_prediction(self, df):
        """Fallback time prediction using simple rules"""
        if df.empty:
            return 1
        
        # Base time: 30 minutes per 100 transactions
        base_hours = len(df) * 0.5
        
        # Add time for complexity
        complexity_score = 0
        if len(df[df['amount'] % 1 == 0]) > len(df) * 0.3:
            complexity_score += 2  # Many round dollars
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            if df[df['date'].dt.dayofweek >= 5].shape[0] > len(df) * 0.2:
                complexity_score += 2  # Many weekend transactions
        
        total_hours = base_hours + complexity_score
        return max(1, round(total_hours, 1))
    
    def predict_problem_areas(self, df):
        """Identify which account areas are most likely to have issues"""
        if df.empty:
            return {}
        
        problem_areas = {}
        
        # Analyze transaction patterns
        amounts = df['amount'].values
        
        # Look for unusual patterns
        if len(amounts) > 10:
            # High value concentration
            top_10_pct = np.percentile(amounts, 90)
            large_count = len(df[df['amount'] > top_10_pct])
            if large_count > len(df) * 0.3:
                problem_areas['Revenue Recognition'] = min(100, large_count * 10)
            
            # Round dollar concentration
            round_pct = len(df[df['amount'] % 1 == 0]) / len(df)
            if round_pct > 0.5:
                problem_areas['Expense Verification'] = min(100, round_pct * 80)
            
            # Duplicate concentration
            duplicate_count = 0
            for amount in amounts:
                if np.sum(amounts == amount) > 1:
                    duplicate_count += 1
            duplicate_pct = duplicate_count / len(df)
            if duplicate_pct > 0.2:
                problem_areas['Accounts Payable'] = min(100, duplicate_pct * 150)
            
            # Weekend concentration
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                weekend_pct = df[df['date'].dt.dayofweek >= 5].shape[0] / len(df)
                if weekend_pct > 0.2:
                    problem_areas['Cash Transactions'] = min(100, weekend_pct * 150)
        
        # Always include at least basic areas
        if not problem_areas:
            problem_areas['General Ledger'] = 50
            problem_areas['Bank Reconciliation'] = 40
        
        # Sort by risk (highest first)
        return dict(sorted(problem_areas.items(), key=lambda x: x[1], reverse=True))
    
    def suggest_resource_allocation(self, fraud_risk, predicted_hours, problem_areas):
        """Recommend senior vs junior staff allocation"""
        recommendations = []
        
        if fraud_risk > 70:
            recommendations.append({
                'area': 'Fraud Investigation',
                'assigned_to': 'Senior Auditor',
                'reason': f'High fraud risk ({fraud_risk:.0f}%) requires experienced investigator'
            })
        elif fraud_risk > 40:
            recommendations.append({
                'area': 'Fraud Review',
                'assigned_to': 'Senior Auditor',
                'reason': f'Medium fraud risk ({fraud_risk:.0f}%) needs senior oversight'
            })
        
        if predicted_hours > 40:
            recommendations.append({
                'area': 'Project Management',
                'assigned_to': 'Audit Manager',
                'reason': f'Large audit ({predicted_hours:.0f} hours) needs manager oversight'
            })
        
        for area, risk in list(problem_areas.items())[:2]:
            if risk > 70:
                recommendations.append({
                    'area': area,
                    'assigned_to': 'Senior Auditor',
                    'reason': f'High risk area ({risk:.0f}%) requires experienced staff'
                })
            elif risk > 40:
                recommendations.append({
                    'area': area,
                    'assigned_to': 'Senior+Junior Team',
                    'reason': f'Medium risk area ({risk:.0f}%) needs oversight'
                })
        
        if not recommendations:
            recommendations.append({
                'area': 'Standard Audit Procedures',
                'assigned_to': 'Junior Auditor',
                'reason': 'Low risk audit suitable for junior staff'
            })
        
        return recommendations


# Singleton instance
_predictor = None

def get_predictor():
    """Get or create the predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = AuditPredictor()
    return _predictor