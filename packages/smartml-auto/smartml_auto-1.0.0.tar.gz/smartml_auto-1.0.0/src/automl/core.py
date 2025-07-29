"""
AutoML Core Orchestrator
========================

The main AutoMLPredictor class that coordinates all components to provide
a simple, powerful interface for automated machine learning.

Usage:
    import automl
    predictor = automl.train(X, y)
    predictions = predictor.predict(X_new)
"""

import pandas as pd
import numpy as np
import time
import warnings
import joblib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
from datetime import datetime

# Import all our intelligent components
from .utils import validate_input_data, detect_task_type, calculate_basic_stats
from .data_analyzer import DataAnalyzer
from .feature_engineer import FeatureEngineer
from .model_selector import ModelSelector


class AutoMLPredictor:
    """
    Complete AutoML system that automatically analyzes data, engineers features,
    and selects the best model with minimal user input.
    
    This is the main class users interact with - it orchestrates all the
    intelligent components to provide a seamless AutoML experience.
    """
    
    def __init__(self, task: Optional[str] = None, time_budget: Union[str, int] = "medium",
                 quality_target: Optional[float] = None, explain: bool = True, verbose: bool = True):
        """
        Initialize AutoML predictor.
        
        Args:
            task: 'classification', 'regression', or None (auto-detect)
            time_budget: 'fast' (5min), 'medium' (30min), 'thorough' (2h), or int (minutes)
            quality_target: Stop training when this score is reached (0.0-1.0)
            explain: Generate explanations and insights
            verbose: Print progress and results
        """
        self.task = task
        self.time_budget = time_budget
        self.quality_target = quality_target
        self.explain = explain
        self.verbose = verbose
        
        # Component instances
        self.analyzer = DataAnalyzer(verbose=verbose)
        self.feature_engineer = None
        self.model_selector = None
        
        # Results and state
        self.is_fitted = False
        self.data_analysis = None
        self.feature_analysis = None
        self.model_analysis = None
        self.preprocessing_pipeline = None
        self.best_model = None
        self.feature_names_in = []
        self.feature_names_out = []
        
        # Training metadata
        self.training_start_time = None
        self.training_end_time = None
        self.total_training_time = 0
        
    def fit(self, X, y):
        """Train the AutoML system on the provided data."""
        try:
            if self.verbose:
                print("🚀 AutoML Training Started")
                print("=" * 50)
                
            self.training_start_time = time.time()
            
            # Step 1: Data Analysis
            if self.verbose:
                print("\n🔍 Step 1: Analyzing your data...")
            
            self.data_analysis = self.analyzer.analyze(X, y, task=self.task)
            
            # Override task if specified
            if self.task is not None:
                self.data_analysis['task_type'] = self.task
            
            if self.verbose:
                quality_score = self.data_analysis.get('data_quality', {}).get('overall_score', 0)
                print(f"   📊 Dataset: {self.data_analysis['n_samples']} samples, {self.data_analysis['n_features']} features")
                print(f"   🎯 Task: {self.data_analysis['task_type']}")
                print(f"   ⭐ Data Quality: {quality_score:.2f}/1.0")
            
            # Step 2: Feature Engineering
            if self.verbose:
                print("\n⚙️  Step 2: Engineering features...")
                
            self.feature_engineer = FeatureEngineer(
                analyzer_results=self.data_analysis, 
                verbose=self.verbose
            )
            
            # Get clean, validated data
            X_clean, y_clean = validate_input_data(X, y)
            self.feature_names_in = list(X_clean.columns)
            
            # Transform data
            X_processed, self.preprocessing_pipeline = self.feature_engineer.fit_transform(X_clean, y_clean)
            self.feature_names_out = self.feature_engineer.feature_names_out
            self.feature_analysis = self.feature_engineer.get_preprocessing_info()
            
            # Step 3: Model Selection
            if self.verbose:
                print("\n🤖 Step 3: Training and selecting models...")
                
            self.model_selector = ModelSelector(
                analyzer_results=self.data_analysis,
                verbose=self.verbose
            )
            
            model_results = self.model_selector.fit(
                X_processed, y_clean,
                task=self.data_analysis['task_type'],
                time_budget=self.time_budget,
                quality_target=self.quality_target,
                analyzer_results=self.data_analysis
            )
            
            self.model_analysis = model_results
            self.best_model = model_results['best_model']
            
            # Step 4: Finalization
            self.training_end_time = time.time()
            self.total_training_time = self.training_end_time - self.training_start_time
            self.is_fitted = True
            
            if self.verbose:
                print(f"\n✅ AutoML Training Complete!")
                print(f"   ⏱️  Total time: {self.total_training_time:.1f} seconds")
                print(f"   🏆 Best model: {model_results['best_algorithm']}")
                print(f"   📈 Best score: {model_results['best_score']:.4f}")
            
            return self
            
        except Exception as e:
            error_msg = f"AutoML training failed: {str(e)}"
            if self.verbose:
                print(f"\n❌ {error_msg}")
            
            self.is_fitted = False
            self.training_end_time = time.time()
            if self.training_start_time:
                self.total_training_time = self.training_end_time - self.training_start_time
                
            raise RuntimeError(error_msg) from e
    
    def predict(self, X):
        """Make predictions on new data."""
        if not self.is_fitted:
            raise ValueError("AutoML predictor not fitted. Call fit() first.")
        
        if self.best_model is None:
            raise ValueError("No trained model available.")
        
        try:
            # Validate and preprocess new data
            X_clean, _ = validate_input_data(X, pd.Series(range(len(X))))
            
            # Ensure feature consistency
            missing_features = set(self.feature_names_in) - set(X_clean.columns)
            if missing_features:
                raise ValueError(f"Missing features in prediction data: {missing_features}")
            
            # Select and reorder features
            X_clean = X_clean[self.feature_names_in]
            
            # Apply preprocessing
            X_processed = self.preprocessing_pipeline.transform(X_clean)
            
            # Make predictions
            predictions = self.best_model.predict(X_processed)
            
            return predictions
            
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {str(e)}") from e

    def summary(self):
        """Print comprehensive summary of AutoML results."""
        if not self.is_fitted:
            print("❌ AutoML predictor not fitted. Call fit() first.")
            return
        
        try:
            print("\n" + "=" * 60)
            print("🤖 AUTOML SUMMARY")
            print("=" * 60)
            
            # Data overview
            print(f"\n📊 DATA OVERVIEW:")
            print(f"   Dataset: {self.data_analysis['n_samples']:,} samples, {self.data_analysis['n_features']} features")
            print(f"   Task: {self.data_analysis['task_type']}")
            print(f"   Data Quality: {self.data_analysis.get('data_quality', {}).get('overall_score', 0):.2f}/1.0")
            
            # Model performance
            print(f"\n🏆 MODEL PERFORMANCE:")
            print(f"   Best Algorithm: {self.model_analysis['best_algorithm']}")
            
            task_type = self.data_analysis['task_type']
            score_name = 'Accuracy' if task_type == 'classification' else 'R² Score'
            print(f"   {score_name}: {self.model_analysis['best_score']:.4f}")
            
            print(f"   Training Time: {self.total_training_time:.1f} seconds")
            print(f"   Models Tried: {self.model_analysis['models_tried']}")
            
            # Quick usage guide
            print(f"\n🚀 USAGE:")
            print(f"   predictions = predictor.predict(X_new)")
            if task_type == 'classification':
                print(f"   probabilities = predictor.predict_proba(X_new)")
            print(f"   predictor.save('my_model.pkl')")
            
        except Exception as e:
            print(f"❌ Could not generate summary: {str(e)}")

    def predict_proba(self, X):
        """Get prediction probabilities (classification only)."""
        if not self.is_fitted:
            raise ValueError("AutoML predictor not fitted. Call fit() first.")
        
        if self.data_analysis.get('task_type') != 'classification':
            raise ValueError("predict_proba only available for classification tasks")
        
        if not hasattr(self.best_model, 'predict_proba'):
            raise ValueError("Best model does not support probability prediction")
        
        try:
            X_clean, _ = validate_input_data(X, pd.Series(range(len(X))))
            X_clean = X_clean[self.feature_names_in]
            X_processed = self.preprocessing_pipeline.transform(X_clean)
            probabilities = self.best_model.predict_proba(X_processed)
            return probabilities
        except Exception as e:
            raise RuntimeError(f"Probability prediction failed: {str(e)}") from e

    def save(self, filepath: str):
        """Save the fitted AutoML predictor to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted predictor. Call fit() first.")
        
        try:
            save_data = {
                'automl_version': '1.0.0',
                'save_timestamp': datetime.now(),
                'task': self.data_analysis['task_type'],
                'best_model': self.best_model,
                'preprocessing_pipeline': self.preprocessing_pipeline,
                'feature_names_in': self.feature_names_in,
                'data_analysis': self.data_analysis,
                'model_analysis': self.model_analysis,
                'total_training_time': self.total_training_time
            }
            
            joblib.dump(save_data, filepath)
            
            if self.verbose:
                print(f"✅ Model saved to {filepath}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to save model: {str(e)}") from e


def train(X, y, task: Optional[str] = None, time_budget: Union[str, int] = "medium",
          quality_target: Optional[float] = None, explain: bool = True, verbose: bool = True):
    """Train an AutoML model on your data."""
    predictor = AutoMLPredictor(
        task=task,
        time_budget=time_budget,
        quality_target=quality_target,
        explain=explain,
        verbose=verbose
    )
    
    predictor.fit(X, y)
    return predictor
