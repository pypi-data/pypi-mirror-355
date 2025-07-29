"""
AutoML Model Selector
====================

Intelligent model selection that uses DataAnalyzer recommendations and
preprocessed data to train and compare multiple algorithms, selecting
the best performer within time and quality constraints.
"""

import pandas as pd
import numpy as np
import time
import warnings
from typing import Dict, List, Any, Tuple, Optional, Union
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

# Optional dependencies with graceful fallbacks
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

# Import our foundation modules
from .utils import validate_input_data, detect_task_type


class ModelSelector:
    """
    Intelligent model selection that trains and compares multiple algorithms.
    
    Uses DataAnalyzer recommendations and handles time budgets while finding
    the best performing model through cross-validation.
    """
    
    def __init__(self, analyzer_results: Optional[Dict] = None, verbose: bool = True):
        """
        Initialize the ModelSelector.
        
        Args:
            analyzer_results: Results from DataAnalyzer.analyze()
            verbose: Whether to print training progress
        """
        self.analyzer_results = analyzer_results
        self.verbose = verbose
        
        # Results storage
        self.models_tried = []
        self.best_model = None
        self.best_score = -np.inf
        self.best_algorithm = None
        self.training_time = 0
        self.cv_results = {}
        
        # Time management
        self.start_time = None
        self.time_budget_seconds = 0
        
    def fit(self, X_train, y_train, X_val=None, y_val=None, 
            task: Optional[str] = None, time_budget: Union[str, int] = "medium",
            quality_target: Optional[float] = None, analyzer_results: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Train and select the best model.
        
        Args:
            X_train: Training features (preprocessed)
            y_train: Training target
            X_val: Optional validation features
            y_val: Optional validation target
            task: Task type ('classification' or 'regression')
            time_budget: Time limit ('fast', 'medium', 'thorough', or minutes as int)
            quality_target: Stop training when this score is reached
            analyzer_results: DataAnalyzer results for algorithm recommendations
            
        Returns:
            Dict with training results and best model info
        """
        try:
            if self.verbose:
                print("🤖 Starting intelligent model selection...")
            
            self.start_time = time.time()
            
            # Setup
            if analyzer_results is not None:
                self.analyzer_results = analyzer_results
            
            # Parse time budget
            self.time_budget_seconds = self._parse_time_budget(time_budget)
            
            # Detect task if not provided
            if task is None:
                task = detect_task_type(pd.Series(y_train))
            
            # Get algorithm recommendations
            algorithms = self._get_algorithms_to_try(task)
            
            if self.verbose:
                print(f"   🎯 Task: {task}")
                print(f"   ⏱️  Time budget: {self.time_budget_seconds // 60} minutes")
                print(f"   🔧 Algorithms to try: {algorithms}")
            
            # Train and evaluate models
            for i, algorithm in enumerate(algorithms):
                # Check time budget
                elapsed = time.time() - self.start_time
                if elapsed > self.time_budget_seconds:
                    if self.verbose:
                        print(f"   ⏰ Time budget exceeded, stopping early")
                    break
                
                if self.verbose:
                    progress = (i + 1) / len(algorithms) * 100
                    print(f"   [{progress:.0f}%] Training {algorithm}...")
                
                # Train and evaluate model
                model_result = self._train_and_evaluate_model(
                    algorithm, task, X_train, y_train, X_val, y_val
                )
                
                if model_result['success']:
                    self.models_tried.append(model_result)
                    
                    if self.verbose:
                        score_name = 'accuracy' if task == 'classification' else 'r2_score'
                        score_value = model_result['scores'].get(score_name, model_result.get('cv_score_mean', 0))
                        print(f"      {score_name}: {score_value:.4f}")
                    
                    # Check if this is the best model
                    current_score = model_result['cv_score_mean']
                    if current_score > self.best_score:
                        self.best_score = current_score
                        self.best_model = model_result['model']
                        self.best_algorithm = algorithm
                        
                        if self.verbose:
                            print(f"      🎯 New best model!")
                        
                        # Check quality target
                        if quality_target and current_score >= quality_target:
                            if self.verbose:
                                print(f"   ✅ Quality target ({quality_target:.3f}) reached!")
                            break
                else:
                    if self.verbose:
                        print(f"      ❌ Failed: {model_result.get('error', 'Unknown error')}")
            
            # Calculate total training time
            self.training_time = time.time() - self.start_time
            
            # Prepare results
            results = self._prepare_results(task)
            
            if self.verbose:
                self._print_results_summary(results)
            
            return results
            
        except Exception as e:
            error_msg = f"Model selection failed: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'best_model': None,
                'best_algorithm': 'none',
                'best_score': 0.0,
                'models_tried': 0
            }
    
    def _parse_time_budget(self, time_budget: Union[str, int]) -> int:
        """Convert time budget to seconds."""
        if isinstance(time_budget, int):
            return time_budget * 60  # Convert minutes to seconds
        elif time_budget == "fast":
            return 5 * 60  # 5 minutes
        elif time_budget == "medium":
            return 30 * 60  # 30 minutes
        elif time_budget == "thorough":
            return 120 * 60  # 2 hours
        else:
            return 30 * 60  # Default to 30 minutes
    
    def _get_algorithms_to_try(self, task: str) -> List[str]:
        """Get list of algorithms to try based on recommendations and availability."""
        # Get recommendations from analyzer if available
        if self.analyzer_results and 'recommended_algorithms' in self.analyzer_results:
            recommended = self.analyzer_results['recommended_algorithms']
        else:
            # Fallback recommendations
            if task == 'classification':
                recommended = ['random_forest', 'logistic_regression', 'svm']
            else:
                recommended = ['random_forest', 'linear_regression', 'ridge']
        
        # Filter by availability and add fallbacks
        available_algorithms = []
        
        for alg in recommended:
            if self._is_algorithm_available(alg):
                available_algorithms.append(alg)
        
        # Ensure we have at least basic algorithms
        basic_algorithms = {
            'classification': ['random_forest', 'logistic_regression'],
            'regression': ['random_forest', 'linear_regression']
        }
        
        for basic_alg in basic_algorithms[task]:
            if basic_alg not in available_algorithms:
                available_algorithms.append(basic_alg)
        
        # Add some additional good algorithms if time permits
        additional_algorithms = {
            'classification': ['naive_bayes', 'knn'],
            'regression': ['ridge', 'knn']
        }
        
        for add_alg in additional_algorithms[task]:
            if add_alg not in available_algorithms and len(available_algorithms) < 5:
                available_algorithms.append(add_alg)
        
        return available_algorithms[:6]  # Limit to 6 algorithms maximum
    
    def _is_algorithm_available(self, algorithm: str) -> bool:
        """Check if algorithm is available (dependencies installed)."""
        if algorithm in ['xgboost']:
            return HAS_XGBOOST
        elif algorithm in ['lightgbm']:
            return HAS_LIGHTGBM
        else:
            return True  # All sklearn algorithms are available
    
    def _train_and_evaluate_model(self, algorithm: str, task: str, 
                                X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        """Train and evaluate a single model."""
        try:
            model_start_time = time.time()
            
            # Create model
            model = self._create_model(algorithm, task)
            if model is None:
                return {'success': False, 'error': f'Could not create {algorithm} model'}
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate with cross-validation
            cv_scores = self._evaluate_model_cv(model, X_train, y_train, task)
            
            # Evaluate on validation set if provided
            val_scores = {}
            if X_val is not None and y_val is not None:
                val_scores = self._evaluate_model_validation(model, X_val, y_val, task)
            
            # Calculate training time
            training_time = time.time() - model_start_time
            
            return {
                'success': True,
                'algorithm': algorithm,
                'model': model,
                'cv_scores': cv_scores,
                'cv_score_mean': np.mean(cv_scores),
                'cv_score_std': np.std(cv_scores),
                'validation_scores': val_scores,
                'scores': val_scores if val_scores else {'primary_score': np.mean(cv_scores)},
                'training_time': training_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'algorithm': algorithm,
                'error': str(e),
                'training_time': time.time() - model_start_time if 'model_start_time' in locals() else 0
            }
    
    def _create_model(self, algorithm: str, task: str):
        """Create model instance based on algorithm and task."""
        try:
            if task == 'classification':
                if algorithm == 'random_forest':
                    return RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1)
                elif algorithm == 'logistic_regression':
                    return LogisticRegression(random_state=42, max_iter=1000)
                elif algorithm == 'svm':
                    return SVC(random_state=42, probability=True)
                elif algorithm == 'naive_bayes':
                    return GaussianNB()
                elif algorithm == 'knn':
                    return KNeighborsClassifier(n_neighbors=5)
                elif algorithm == 'decision_tree':
                    return DecisionTreeClassifier(random_state=42)
                elif algorithm == 'xgboost' and HAS_XGBOOST:
                    return xgb.XGBClassifier(random_state=42, eval_metric='logloss', verbosity=0)
                elif algorithm == 'lightgbm' and HAS_LIGHTGBM:
                    return lgb.LGBMClassifier(random_state=42, verbosity=-1)
                elif algorithm == 'gradient_boosting':
                    from sklearn.ensemble import GradientBoostingClassifier
                    return GradientBoostingClassifier(random_state=42)
                    
            else:  # regression
                if algorithm == 'random_forest':
                    return RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1)
                elif algorithm == 'linear_regression':
                    return LinearRegression()
                elif algorithm == 'ridge':
                    return Ridge(random_state=42)
                elif algorithm == 'lasso':
                    return Lasso(random_state=42)
                elif algorithm == 'svm':
                    return SVR()
                elif algorithm == 'knn':
                    return KNeighborsRegressor(n_neighbors=5)
                elif algorithm == 'decision_tree':
                    return DecisionTreeRegressor(random_state=42)
                elif algorithm == 'xgboost' and HAS_XGBOOST:
                    return xgb.XGBRegressor(random_state=42, verbosity=0)
                elif algorithm == 'lightgbm' and HAS_LIGHTGBM:
                    return lgb.LGBMRegressor(random_state=42, verbosity=-1)
                elif algorithm == 'gradient_boosting':
                    from sklearn.ensemble import GradientBoostingRegressor
                    return GradientBoostingRegressor(random_state=42)
            
            return None
            
        except Exception:
            return None
    
    def _evaluate_model_cv(self, model, X, y, task: str, cv_folds: int = 5) -> List[float]:
        """Evaluate model using cross-validation."""
        try:
            # Choose appropriate cross-validation strategy
            if task == 'classification':
                cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
                scoring = 'accuracy'
            else:
                cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
                scoring = 'r2'
            
            # Perform cross-validation
            scores = cross_val_score(model, X, y.values if hasattr(y, "values") else y, cv=cv, scoring=scoring, n_jobs=1)
            return scores.tolist()
            
        except Exception as e:
            # Fallback to simple train-test evaluation
            try:
                from sklearn.model_selection import train_test_split
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42,
                    stratify=y if task == 'classification' else None
                )
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                if task == 'classification':
                    score = accuracy_score(y_test, predictions)
                else:
                    score = r2_score(y_test, predictions)
                
                return [score]
                
            except Exception:
                return [0.0]
    
    def _evaluate_model_validation(self, model, X_val, y_val, task: str) -> Dict[str, float]:
        """Evaluate model on validation set with multiple metrics."""
        try:
            predictions = model.predict(X_val)
            scores = {}
            
            if task == 'classification':
                scores['accuracy'] = accuracy_score(y_val, predictions)
                
                # Additional metrics for binary classification
                unique_classes = np.unique(y_val)
                if len(unique_classes) == 2:
                    scores['precision'] = precision_score(y_val, predictions, average='binary')
                    scores['recall'] = recall_score(y_val, predictions, average='binary')
                    scores['f1_score'] = f1_score(y_val, predictions, average='binary')
                    
                    # ROC AUC if model supports probability prediction
                    if hasattr(model, 'predict_proba'):
                        try:
                            probabilities = model.predict_proba(X_val)[:, 1]
                            scores['roc_auc'] = roc_auc_score(y_val, probabilities)
                        except Exception:
                            pass
                else:
                    # Multiclass metrics
                    scores['precision'] = precision_score(y_val, predictions, average='weighted')
                    scores['recall'] = recall_score(y_val, predictions, average='weighted')
                    scores['f1_score'] = f1_score(y_val, predictions, average='weighted')
                    
            else:  # regression
                scores['r2_score'] = r2_score(y_val, predictions)
                scores['mean_squared_error'] = mean_squared_error(y_val, predictions)
                scores['mean_absolute_error'] = mean_absolute_error(y_val, predictions)
                scores['rmse'] = np.sqrt(scores['mean_squared_error'])
            
            return scores
            
        except Exception as e:
            # Return minimal scores
            if task == 'classification':
                return {'accuracy': 0.0}
            else:
                return {'r2_score': 0.0}
    
    def _prepare_results(self, task: str) -> Dict[str, Any]:
        """Prepare comprehensive results dictionary."""
        return {
            'success': len(self.models_tried) > 0,
            'best_model': self.best_model,
            'best_algorithm': self.best_algorithm,
            'best_score': self.best_score,
            'task_type': task,
            'models_tried': len(self.models_tried),
            'training_time': self.training_time,
            'all_results': self.models_tried,
            'model_comparison': self._create_model_comparison(),
            'recommendations': self._generate_recommendations()
        }
    
    def _create_model_comparison(self) -> pd.DataFrame:
        """Create comparison table of all models tried."""
        try:
            if not self.models_tried:
                return pd.DataFrame()
            
            comparison_data = []
            for result in self.models_tried:
                if result['success']:
                    row = {
                        'algorithm': result['algorithm'],
                        'cv_score_mean': result['cv_score_mean'],
                        'cv_score_std': result['cv_score_std'],
                        'training_time': result['training_time']
                    }
                    
                    # Add validation scores if available
                    if result['validation_scores']:
                        for metric, score in result['validation_scores'].items():
                            row[f'val_{metric}'] = score
                    
                    comparison_data.append(row)
            
            if comparison_data:
                df = pd.DataFrame(comparison_data)
                return df.sort_values('cv_score_mean', ascending=False)
            else:
                return pd.DataFrame()
                
        except Exception:
            return pd.DataFrame()
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on results."""
        recommendations = []
        
        try:
            if self.best_score < 0.7:
                recommendations.append("Consider collecting more training data")
                recommendations.append("Review feature engineering - current features may not be predictive")
            
            if self.training_time > self.time_budget_seconds * 0.8:
                recommendations.append("Consider using faster algorithms for quicker iteration")
            
            if len(self.models_tried) < 3:
                recommendations.append("Increase time budget to try more algorithms")
            
            # Algorithm-specific recommendations
            if self.best_algorithm == 'random_forest':
                recommendations.append("Random Forest performed best - consider tuning n_estimators and max_depth")
            elif self.best_algorithm in ['xgboost', 'lightgbm']:
                recommendations.append("Gradient boosting performed best - consider hyperparameter tuning")
            elif self.best_algorithm == 'logistic_regression':
                recommendations.append("Linear model performed best - data may have linear relationships")
            
            if not recommendations:
                recommendations.append("Model performance looks good - ready for production!")
                
        except Exception:
            recommendations.append("Review model selection results manually")
        
        return recommendations
    
    def _print_results_summary(self, results: Dict[str, Any]) -> None:
        """Print comprehensive results summary."""
        try:
            print(f"\n🎯 Model Selection Results:")
            print(f"   🏆 Best Algorithm: {results['best_algorithm']}")
            print(f"   📊 Best Score: {results['best_score']:.4f}")
            print(f"   ⏱️  Total Time: {results['training_time']:.1f}s")
            print(f"   🔧 Models Tried: {results['models_tried']}")
            
            # Print model comparison if available
            comparison = results.get('model_comparison')
            if isinstance(comparison, pd.DataFrame) and not comparison.empty:
                print(f"\n📋 Model Comparison:")
                for _, row in comparison.head(3).iterrows():
                    print(f"   {row['algorithm']}: {row['cv_score_mean']:.4f} (±{row['cv_score_std']:.4f})")
            
            # Print recommendations
            recommendations = results.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations[:3]:
                    print(f"   • {rec}")
                    
        except Exception:
            print("   📋 Results summary not available")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about the selected model."""
        if self.best_model is None:
            return {'error': 'No model selected'}
        
        try:
            info = {
                'algorithm': self.best_algorithm,
                'best_score': self.best_score,
                'training_time': self.training_time,
                'model_parameters': self.best_model.get_params(),
                'feature_importance': self._get_feature_importance(),
                'model_type': type(self.best_model).__name__
            }
            
            return info
            
        except Exception as e:
            return {'error': f'Could not get model info: {str(e)}'}
    
    def _get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if available."""
        try:
            if hasattr(self.best_model, 'feature_importances_'):
                # Tree-based models
                importances = self.best_model.feature_importances_
                return {f'feature_{i}': float(imp) for i, imp in enumerate(importances)}
            elif hasattr(self.best_model, 'coef_'):
                # Linear models
                coef = self.best_model.coef_
                if coef.ndim > 1:
                    coef = coef[0]  # Take first class for multiclass
                return {f'feature_{i}': float(abs(c)) for i, c in enumerate(coef)}
            else:
                return None
                
        except Exception:
            return None


# Test section - comprehensive testing of the ModelSelector
if __name__ == "__main__":
    print("🧪 Testing AutoML Model Selector")
    print("=" * 60)
    
    # Test 1: Classification with recommended algorithms
    print("\n📊 Test 1: Classification Model Selection")
    try:
        from sklearn.datasets import make_classification
        from sklearn.model_selection import train_test_split
        
        # Create classification dataset
        X, y = make_classification(n_samples=500, n_features=10, n_informative=5, 
                                 n_redundant=2, n_classes=2, random_state=42)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Mock analyzer results
        mock_analysis = {
            'recommended_algorithms': ['random_forest', 'logistic_regression', 'xgboost'],
            'task_type': 'classification',
            'n_samples': 400,
            'n_features': 10
        }
        
        # Test model selection
        selector = ModelSelector(analyzer_results=mock_analysis, verbose=True)
        results = selector.fit(X_train, y_train, X_test, y_test, 
                             task='classification', time_budget='fast')
        
        print(f"✅ Classification test complete!")
        print(f"   Best model: {results['best_algorithm']}")
        print(f"   Best score: {results['best_score']:.4f}")
        
        # Test model info
        model_info = selector.get_model_info()
        if 'error' not in model_info:
            print(f"   Model type: {model_info['model_type']}")
        
    except Exception as e:
        print(f"❌ Classification test failed: {e}")
    
    # Test 2: Regression with time budget
    print("\n📈 Test 2: Regression with Time Budget")
    try:
        from sklearn.datasets import make_regression
        
        # Create regression dataset
        X, y = make_regression(n_samples=300, n_features=8, noise=0.1, random_state=42)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Test with different time budget
        selector = ModelSelector(verbose=True)
        results = selector.fit(X_train, y_train, X_test, y_test,
                             task='regression', time_budget=2)  # 2 minutes
        
        print(f"✅ Regression test complete!")
        print(f"   Models tried: {results['models_tried']}")
        print(f"   Training time: {results['training_time']:.1f}s")
        
    except Exception as e:
        print(f"❌ Regression test failed: {e}")
    
    # Test 3: Small dataset with quality target
    print("\n🎯 Test 3: Quality Target Achievement")
    try:
        # Create easy classification problem
        X, y = make_classification(n_samples=150, n_features=5, n_informative=4,
                                 n_redundant=0, n_clusters_per_class=1, random_state=42)
        
        selector = ModelSelector(verbose=True)
        results = selector.fit(X, y, task='classification', 
                             time_budget='medium', quality_target=0.85)
        
        print(f"✅ Quality target test complete!")
        print(f"   Target reached: {results['best_score'] >= 0.85}")
        
    except Exception as e:
        print(f"❌ Quality target test failed: {e}")
    
    # Test 4: Error handling with problematic data
    print("\n⚠️  Test 4: Error Handling")
    try:
        # Create problematic dataset
        X_bad = np.array([[1, 2], [1, 2], [1, 2]])  # All same values
        y_bad = np.array([0, 0, 0])  # All same class
        
        selector = ModelSelector(verbose=True)
        results = selector.fit(X_bad, y_bad, task='classification', time_budget='fast')
        
        print(f"✅ Error handling test complete!")
        print(f"   Handled gracefully: {results.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 5: Integration test with all components
    print("\n🔗 Test 5: Full Integration Test")
    try:
        from .data_analyzer import DataAnalyzer
        from .feature_engineer import FeatureEngineer
        
        # Create realistic dataset
        X, y = make_classification(n_samples=200, n_features=6, n_informative=4, random_state=42)
        X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(6)])
        
        # Add categorical feature
        X_df['category'] = np.random.choice(['A', 'B', 'C'], size=200)
        y_series = pd.Series(y)
        
        # Full pipeline
        analyzer = DataAnalyzer(verbose=False)
        analysis = analyzer.analyze(X_df, y_series)
        
        engineer = FeatureEngineer(analyzer_results=analysis, verbose=False)
        X_processed, pipeline = engineer.fit_transform(X_df, y_series)
        
        selector = ModelSelector(analyzer_results=analysis, verbose=True)
        results = selector.fit(X_processed, y_series, task='classification', time_budget='fast')
        
        print(f"✅ Full integration test complete!")
        print(f"   Pipeline: DataAnalyzer → FeatureEngineer → ModelSelector")
        print(f"   Final model: {results['best_algorithm']}")
        print(f"   Final score: {results['best_score']:.4f}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    print("\n🎉 Model Selector testing completed!")
    print("\n💡 Next steps:")
    print("   1. Implement automl/core.py to orchestrate everything")
    print("   2. Test with real-world datasets")
    print("   3. Add hyperparameter tuning for best models")
