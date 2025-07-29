"""Machine learning models for credit risk assessment."""

import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)


class BaseMLModel:
    """Base class for machine learning models."""
    
    def __init__(self):
        """Initialize base ML model."""
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.performance_metrics = {}
    
    def prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for model input."""
        raise NotImplementedError("Subclasses must implement prepare_features")
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the model."""
        raise NotImplementedError("Subclasses must implement train")
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction."""
        raise NotImplementedError("Subclasses must implement predict")


class RandomForestModel(BaseMLModel):
    """Random Forest model for credit risk prediction."""
    
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        """Initialize Random Forest model."""
        super().__init__()
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2
        )
        self.feature_names = [
            'credit_score', 'monthly_income', 'monthly_debt', 'loan_amount',
            'employment_length', 'dti_ratio', 'loan_to_income_ratio'
        ]
    
    def prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for Random Forest model."""
        features = []
        
        # Extract and normalize features
        features.append(data.get('credit_score', 650) / 850.0)  # Normalize to 0-1
        features.append(np.log1p(data.get('monthly_income', 3000)))  # Log transform
        features.append(np.log1p(data.get('monthly_debt', 1000)))  # Log transform
        features.append(np.log1p(data.get('loan_amount', 10000)))  # Log transform
        features.append(min(data.get('employment_length', 2), 20) / 20.0)  # Cap and normalize
        
        # Calculate derived features
        monthly_income = data.get('monthly_income', 3000)
        monthly_debt = data.get('monthly_debt', 1000)
        dti_ratio = monthly_debt / monthly_income if monthly_income > 0 else 0.5
        features.append(min(dti_ratio, 1.0))  # Cap DTI at 1.0
        
        loan_amount = data.get('loan_amount', 10000)
        annual_income = data.get('annual_income', monthly_income * 12)
        lti_ratio = loan_amount / annual_income if annual_income > 0 else 0.5
        features.append(min(lti_ratio, 5.0) / 5.0)  # Cap and normalize
        
        return np.array(features).reshape(1, -1)
    
    def train(self, training_data: List[Dict[str, Any]], labels: List[int]) -> None:
        """
        Train the Random Forest model.
        
        Args:
            training_data: List of application dictionaries
            labels: List of labels (0 = approved, 1 = declined)
        """
        try:
            # Prepare features
            X = []
            for data in training_data:
                features = self.prepare_features(data).flatten()
                X.append(features)
            
            X = np.array(X)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True
            
            # Calculate performance metrics
            y_pred = self.model.predict(X_test_scaled)
            self.performance_metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
            }
            
            logger.info(f"Random Forest model trained. Accuracy: {self.performance_metrics['accuracy']:.3f}")
            
        except Exception as e:
            logger.error(f"Error training Random Forest model: {str(e)}")
            self.is_trained = False
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using Random Forest model."""
        if not self.is_trained:
            logger.warning("Model not trained. Using default prediction.")
            return {
                'prediction': 0,
                'probability': 0.5,
                'confidence': 'low',
                'model_used': 'default'
            }
        
        try:
            # Prepare features
            X = self.prepare_features(data)
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Determine confidence
            max_prob = max(probabilities)
            if max_prob > 0.8:
                confidence = 'high'
            elif max_prob > 0.6:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            return {
                'prediction': int(prediction),
                'probability': float(probabilities[1]),  # Probability of decline
                'confidence': confidence,
                'model_used': 'random_forest'
            }
            
        except Exception as e:
            logger.error(f"Error making Random Forest prediction: {str(e)}")
            return {
                'prediction': 0,
                'probability': 0.5,
                'confidence': 'low',
                'model_used': 'error_fallback'
            }


class LogisticRegressionModel(BaseMLModel):
    """Logistic Regression model for credit risk prediction."""
    
    def __init__(self, random_state: int = 42):
        """Initialize Logistic Regression model."""
        super().__init__()
        self.model = LogisticRegression(
            random_state=random_state,
            max_iter=1000,
            C=1.0,
            solver='liblinear'
        )
        self.feature_names = [
            'credit_score', 'monthly_income', 'monthly_debt', 'loan_amount',
            'employment_length', 'dti_ratio', 'loan_to_income_ratio'
        ]
    
    def prepare_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for Logistic Regression model."""
        features = []
        
        # Extract features (similar to Random Forest but without log transforms)
        features.append(data.get('credit_score', 650))
        features.append(data.get('monthly_income', 3000))
        features.append(data.get('monthly_debt', 1000))
        features.append(data.get('loan_amount', 10000))
        features.append(data.get('employment_length', 2))
        
        # Calculate derived features
        monthly_income = data.get('monthly_income', 3000)
        monthly_debt = data.get('monthly_debt', 1000)
        dti_ratio = monthly_debt / monthly_income if monthly_income > 0 else 0.5
        features.append(dti_ratio)
        
        loan_amount = data.get('loan_amount', 10000)
        annual_income = data.get('annual_income', monthly_income * 12)
        lti_ratio = loan_amount / annual_income if annual_income > 0 else 0.5
        features.append(lti_ratio)
        
        return np.array(features).reshape(1, -1)
    
    def train(self, training_data: List[Dict[str, Any]], labels: List[int]) -> None:
        """
        Train the Logistic Regression model.
        
        Args:
            training_data: List of application dictionaries
            labels: List of labels (0 = approved, 1 = declined)
        """
        try:
            # Prepare features
            X = []
            for data in training_data:
                features = self.prepare_features(data).flatten()
                X.append(features)
            
            X = np.array(X)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features (important for Logistic Regression)
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            self.is_trained = True
            
            # Calculate performance metrics
            y_pred = self.model.predict(X_test_scaled)
            self.performance_metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'coefficients': dict(zip(self.feature_names, self.model.coef_[0]))
            }
            
            logger.info(f"Logistic Regression model trained. Accuracy: {self.performance_metrics['accuracy']:.3f}")
            
        except Exception as e:
            logger.error(f"Error training Logistic Regression model: {str(e)}")
            self.is_trained = False
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using Logistic Regression model."""
        if not self.is_trained:
            logger.warning("Model not trained. Using default prediction.")
            return {
                'prediction': 0,
                'probability': 0.5,
                'confidence': 'low',
                'model_used': 'default'
            }
        
        try:
            # Prepare features
            X = self.prepare_features(data)
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Determine confidence
            max_prob = max(probabilities)
            if max_prob > 0.8:
                confidence = 'high'
            elif max_prob > 0.6:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            return {
                'prediction': int(prediction),
                'probability': float(probabilities[1]),  # Probability of decline
                'confidence': confidence,
                'model_used': 'logistic_regression'
            }
            
        except Exception as e:
            logger.error(f"Error making Logistic Regression prediction: {str(e)}")
            return {
                'prediction': 0,
                'probability': 0.5,
                'confidence': 'low',
                'model_used': 'error_fallback'
            }
