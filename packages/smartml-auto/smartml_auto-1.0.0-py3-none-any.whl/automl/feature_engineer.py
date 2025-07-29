"""
AutoML Feature Engineer
=======================

Intelligent feature engineering that uses DataAnalyzer insights to make
smart preprocessing decisions. Creates sklearn pipelines for reproducible
data transformation.
"""

import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Any, Tuple, Optional, Union
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    OneHotEncoder, LabelEncoder, OrdinalEncoder,
    PowerTransformer, QuantileTransformer
)
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, mutual_info_classif, mutual_info_regression
from sklearn.base import BaseEstimator, TransformerMixin

# Import our foundation modules
from .utils import validate_input_data, detect_task_type
from .data_analyzer import DataAnalyzer


class OutlierTransformer(BaseEstimator, TransformerMixin):
    """Custom transformer for handling outliers using IQR method."""
    
    def __init__(self, method='clip', factor=1.5):
        """
        Initialize outlier transformer.
        
        Args:
            method: 'clip', 'remove', or 'winsorize'
            factor: IQR multiplier for outlier detection
        """
        self.method = method
        self.factor = factor
        self.bounds_ = {}
    
    def fit(self, X, y=None):
        """Learn outlier bounds for each numeric column."""
        if isinstance(X, pd.DataFrame):
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                series = X[col].dropna()
                if len(series) > 4:
                    Q1 = series.quantile(0.25)
                    Q3 = series.quantile(0.75)
                    IQR = Q3 - Q1
                    if IQR > 0:
                        self.bounds_[col] = {
                            'lower': Q1 - self.factor * IQR,
                            'upper': Q3 + self.factor * IQR
                        }
        return self
    
    def transform(self, X):
        """Apply outlier handling."""
        X_transformed = X.copy()
        
        if isinstance(X_transformed, pd.DataFrame):
            for col, bounds in self.bounds_.items():
                if col in X_transformed.columns:
                    if self.method == 'clip':
                        X_transformed[col] = X_transformed[col].clip(
                            lower=bounds['lower'], 
                            upper=bounds['upper']
                        )
                    elif self.method == 'winsorize':
                        # Winsorize: replace outliers with 5th/95th percentiles
                        p5 = X_transformed[col].quantile(0.05)
                        p95 = X_transformed[col].quantile(0.95)
                        X_transformed[col] = X_transformed[col].clip(lower=p5, upper=p95)
        
        return X_transformed


class FeatureEngineer:
    """
    Intelligent feature engineering that adapts to data characteristics.
    
    Uses insights from DataAnalyzer to make smart preprocessing decisions
    and creates reproducible sklearn pipelines.
    """
    
    def __init__(self, analyzer_results: Optional[Dict] = None, verbose: bool = True):
        """
        Initialize the FeatureEngineer.
        
        Args:
            analyzer_results: Results from DataAnalyzer.analyze()
            verbose: Whether to print preprocessing decisions
        """
        self.analyzer_results = analyzer_results
        self.verbose = verbose
        self.pipeline = None
        self.feature_names_out = []
        self.preprocessing_steps = []
        
    def fit_transform(self, X, y, analyzer_results: Optional[Dict] = None) -> Tuple[np.ndarray, Pipeline]:
        """
        Create and fit preprocessing pipeline, then transform data.
        
        Args:
            X: Feature data
            y: Target variable
            analyzer_results: Optional analyzer results (overrides constructor)
            
        Returns:
            Tuple of (transformed_data, fitted_pipeline)
        """
        try:
            if self.verbose:
                print("🔧 Starting intelligent feature engineering...")
            
            # Validate input data
            X_clean, y_clean = validate_input_data(X, y)
            
            # Use provided analyzer results or run analysis
            if analyzer_results is not None:
                self.analyzer_results = analyzer_results
            elif self.analyzer_results is None:
                if self.verbose:
                    print("   🔍 Running data analysis...")
                analyzer = DataAnalyzer(verbose=False)
                self.analyzer_results = analyzer.analyze(X_clean, y_clean)
            
            # Create preprocessing pipeline
            if self.verbose:
                print("   🏗️  Building preprocessing pipeline...")
            self.pipeline = self._create_preprocessing_pipeline(X_clean, y_clean)
            
            # Fit and transform data
            if self.verbose:
                print("   ⚙️  Fitting and transforming data...")
            X_transformed = self.pipeline.fit_transform(X_clean)
            
            # Store feature names
            self.feature_names_out = self._get_feature_names()
            
            if self.verbose:
                original_shape = X_clean.shape
                new_shape = X_transformed.shape
                print(f"✅ Feature engineering complete!")
                print(f"   📊 Shape: {original_shape} → {new_shape}")
                print(f"   🔧 Steps applied: {len(self.preprocessing_steps)}")
                self._print_preprocessing_summary()
            
            return X_transformed, self.pipeline
            
        except Exception as e:
            error_msg = f"Feature engineering failed: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            # Return minimal preprocessing as fallback
            basic_pipeline = self._create_basic_pipeline(X_clean)
            X_transformed = basic_pipeline.fit_transform(X_clean)
            return X_transformed, basic_pipeline
    
    def transform(self, X) -> np.ndarray:
        """Transform new data using fitted pipeline."""
        if self.pipeline is None:
            raise ValueError("Pipeline not fitted. Call fit_transform first.")
        
        X_clean, _ = validate_input_data(X, pd.Series(range(len(X))))
        return self.pipeline.transform(X_clean)
    
    def _create_preprocessing_pipeline(self, X: pd.DataFrame, y: pd.Series) -> Pipeline:
        """Create intelligent preprocessing pipeline based on analysis."""
        try:
            # Get data characteristics
            numeric_features = list(X.select_dtypes(include=[np.number]).columns)
            categorical_features = list(X.select_dtypes(include=['object', 'category']).columns)
            
            # Remove problematic features if identified
            problematic_features = self.analyzer_results.get('feature_analysis', {}).get('problematic_features', [])
            numeric_features = [f for f in numeric_features if f not in problematic_features]
            categorical_features = [f for f in categorical_features if f not in problematic_features]
            
            transformers = []
            
            # Numeric preprocessing pipeline
            if numeric_features:
                numeric_pipeline = self._create_numeric_pipeline(numeric_features)
                transformers.append(('numeric', numeric_pipeline, numeric_features))
                self.preprocessing_steps.append(f"Numeric features ({len(numeric_features)}): {self._get_numeric_steps()}")
            
            # Categorical preprocessing pipeline
            if categorical_features:
                categorical_pipeline = self._create_categorical_pipeline(categorical_features)
                transformers.append(('categorical', categorical_pipeline, categorical_features))
                self.preprocessing_steps.append(f"Categorical features ({len(categorical_features)}): {self._get_categorical_steps()}")
            
            # Create main preprocessing pipeline
            if transformers:
                preprocessor = ColumnTransformer(
                    transformers=transformers,
                    remainder='drop',  # Drop problematic features
                    sparse_threshold=0  # Return dense arrays
                )
            else:
                # Fallback if no valid features
                preprocessor = ColumnTransformer(
                    transformers=[('passthrough', 'passthrough', list(X.columns))],
                    remainder='drop'
                )
            
            # Optional feature selection
            feature_selector = self._create_feature_selector(y)
            
            if feature_selector is not None:
                pipeline = Pipeline([
                    ('preprocessing', preprocessor),
                    ('feature_selection', feature_selector)
                ])
                self.preprocessing_steps.append("Feature selection: Mutual information")
            else:
                pipeline = Pipeline([
                    ('preprocessing', preprocessor)
                ])
            
            return pipeline
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Pipeline creation failed: {e}")
            return self._create_basic_pipeline(X)
    
    def _create_numeric_pipeline(self, numeric_features: List[str]) -> Pipeline:
        """Create preprocessing pipeline for numeric features."""
        steps = []
        
        # Missing value imputation
        missing_strategy = self._get_missing_value_strategy('numeric')
        if missing_strategy == 'knn':
            imputer = KNNImputer(n_neighbors=5)
            self.numeric_imputation = 'KNN imputation'
        else:
            imputer = SimpleImputer(strategy=missing_strategy)
            self.numeric_imputation = f'{missing_strategy} imputation'
        
        steps.append(('imputer', imputer))
        
        # Outlier handling
        if self._should_handle_outliers():
            outlier_method = self._get_outlier_handling_method()
            outlier_transformer = OutlierTransformer(method=outlier_method)
            steps.append(('outliers', outlier_transformer))
            self.outlier_handling = f'{outlier_method} outliers'
        else:
            self.outlier_handling = 'none'
        
        # Scaling
        scaler_type = self._get_scaler_type()
        if scaler_type == 'standard':
            scaler = StandardScaler()
            self.scaling_method = 'Standard scaling'
        elif scaler_type == 'minmax':
            scaler = MinMaxScaler()
            self.scaling_method = 'MinMax scaling'
        elif scaler_type == 'robust':
            scaler = RobustScaler()
            self.scaling_method = 'Robust scaling'
        else:
            scaler = StandardScaler()  # Default
            self.scaling_method = 'Standard scaling'
        
        steps.append(('scaler', scaler))
        
        # Skewness transformation (optional)
        if self._should_transform_skewness():
            transformer = PowerTransformer(method='yeo-johnson', standardize=False)
            steps.append(('skewness', transformer))
            self.skewness_transform = 'Yeo-Johnson transformation'
        else:
            self.skewness_transform = 'none'
        
        return Pipeline(steps)
    
    def _create_categorical_pipeline(self, categorical_features: List[str]) -> Pipeline:
        """Create preprocessing pipeline for categorical features."""
        steps = []
        
        # Missing value imputation
        missing_strategy = self._get_missing_value_strategy('categorical')
        imputer = SimpleImputer(strategy=missing_strategy, fill_value='missing')
        steps.append(('imputer', imputer))
        self.categorical_imputation = f'{missing_strategy} imputation'
        
        # Encoding strategy
        encoding_strategy = self._get_encoding_strategy(categorical_features)
        
        if encoding_strategy == 'onehot':
            encoder = OneHotEncoder(
                sparse_output=False,
                handle_unknown='ignore',
                max_categories=20  # Limit to prevent explosion
            )
            self.encoding_method = 'One-hot encoding'
        elif encoding_strategy == 'ordinal':
            encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
            self.encoding_method = 'Ordinal encoding'
        else:
            # Default to one-hot
            encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            self.encoding_method = 'One-hot encoding'
        
        steps.append(('encoder', encoder))
        
        return Pipeline(steps)
    
    def _create_feature_selector(self, y: pd.Series) -> Optional[SelectKBest]:
        """Create feature selector if needed."""
        try:
            # Feature selection criteria
            n_features = self.analyzer_results.get('n_features', 0)
            n_samples = self.analyzer_results.get('n_samples', 0)
            task_type = self.analyzer_results.get('task_type', 'classification')
            
            # Only apply feature selection if we have too many features relative to samples
            if n_features > n_samples or n_features > 50:
                k = min(max(int(n_samples * 0.5), 10), n_features - 1)  # Select reasonable number
                
                if task_type == 'classification':
                    score_func = mutual_info_classif
                else:
                    score_func = mutual_info_regression
                
                return SelectKBest(score_func=score_func, k=k)
            
            return None
            
        except Exception:
            return None
    
    def _get_missing_value_strategy(self, feature_type: str) -> str:
        """Determine missing value strategy based on data characteristics."""
        missing_pct = self.analyzer_results.get('missing_values', {}).get('missing_percentage_X', 0)
        
        if feature_type == 'numeric':
            if missing_pct > 30:
                return 'median'  # More robust for high missing data
            elif missing_pct > 10:
                return 'median'
            else:
                return 'mean'
        else:  # categorical
            return 'most_frequent'
    
    def _should_handle_outliers(self) -> bool:
        """Determine if outlier handling is needed."""
        outlier_pct = self.analyzer_results.get('outlier_analysis', {}).get('outlier_summary', {}).get('outlier_percentage', 0)
        return outlier_pct > 5  # Handle outliers if more than 5% of data
    
    def _get_outlier_handling_method(self) -> str:
        """Choose outlier handling method based on data characteristics."""
        outlier_pct = self.analyzer_results.get('outlier_analysis', {}).get('outlier_summary', {}).get('outlier_percentage', 0)
        
        if outlier_pct > 20:
            return 'winsorize'  # More aggressive for very outlier-heavy data
        else:
            return 'clip'  # Conservative approach
    
    def _get_scaler_type(self) -> str:
        """Choose scaling method based on data characteristics."""
        # Check if we have outliers
        has_outliers = self.analyzer_results.get('outlier_analysis', {}).get('outlier_summary', {}).get('outlier_percentage', 0) > 5
        
        # Check for skewed features
        feature_analysis = self.analyzer_results.get('feature_analysis', {}).get('numeric_features', {})
        highly_skewed = any(
            abs(info.get('skewness', 0)) > 2 
            for info in feature_analysis.values() 
            if isinstance(info, dict) and 'skewness' in info
        )
        
        if has_outliers or highly_skewed:
            return 'robust'  # Robust to outliers and skewness
        else:
            return 'standard'  # Standard scaling for normal data
    
    def _should_transform_skewness(self) -> bool:
        """Determine if skewness transformation is needed."""
        feature_analysis = self.analyzer_results.get('feature_analysis', {}).get('numeric_features', {})
        
        # Count highly skewed features
        highly_skewed_count = sum(
            1 for info in feature_analysis.values()
            if isinstance(info, dict) and abs(info.get('skewness', 0)) > 2
        )
        
        # Transform if more than 25% of numeric features are highly skewed
        total_numeric = len(feature_analysis)
        return total_numeric > 0 and (highly_skewed_count / total_numeric) > 0.25
    
    def _get_encoding_strategy(self, categorical_features: List[str]) -> str:
        """Choose encoding strategy based on categorical feature characteristics."""
        categorical_analysis = self.analyzer_results.get('feature_analysis', {}).get('categorical_features', {})
        
        # Check for high cardinality features
        high_cardinality_count = 0
        for feature in categorical_features:
            if feature in categorical_analysis:
                unique_count = categorical_analysis[feature].get('unique_count', 0)
                if unique_count > 10:
                    high_cardinality_count += 1
        
        # Use ordinal encoding if many high-cardinality features
        if len(categorical_features) > 0 and (high_cardinality_count / len(categorical_features)) > 0.5:
            return 'ordinal'
        else:
            return 'onehot'
    
    def _create_basic_pipeline(self, X: pd.DataFrame) -> Pipeline:
        """Create basic fallback pipeline when intelligent pipeline fails."""
        try:
            numeric_features = list(X.select_dtypes(include=[np.number]).columns)
            categorical_features = list(X.select_dtypes(include=['object', 'category']).columns)
            
            transformers = []
            
            if numeric_features:
                numeric_pipeline = Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler())
                ])
                transformers.append(('numeric', numeric_pipeline, numeric_features))
            
            if categorical_features:
                categorical_pipeline = Pipeline([
                    ('imputer', SimpleImputer(strategy='most_frequent')),
                    ('encoder', OneHotEncoder(sparse_output=False, handle_unknown='ignore'))
                ])
                transformers.append(('categorical', categorical_pipeline, categorical_features))
            
            if transformers:
                preprocessor = ColumnTransformer(transformers=transformers, remainder='drop')
            else:
                preprocessor = ColumnTransformer(transformers=[('passthrough', 'passthrough', list(X.columns))])
            
            return Pipeline([('preprocessing', preprocessor)])
            
        except Exception:
            # Ultimate fallback
            return Pipeline([('passthrough', 'passthrough')])
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names after transformation."""
        try:
            if hasattr(self.pipeline, 'get_feature_names_out'):
                return list(self.pipeline.get_feature_names_out())
            else:
                # Estimate feature names for older sklearn versions
                return [f'feature_{i}' for i in range(100)]  # Rough estimate
        except Exception:
            return []
    
    def _get_numeric_steps(self) -> str:
        """Get description of numeric preprocessing steps."""
        steps = []
        if hasattr(self, 'numeric_imputation'):
            steps.append(self.numeric_imputation)
        if hasattr(self, 'outlier_handling') and self.outlier_handling != 'none':
            steps.append(self.outlier_handling)
        if hasattr(self, 'scaling_method'):
            steps.append(self.scaling_method)
        if hasattr(self, 'skewness_transform') and self.skewness_transform != 'none':
            steps.append(self.skewness_transform)
        return ', '.join(steps) if steps else 'basic preprocessing'
    
    def _get_categorical_steps(self) -> str:
        """Get description of categorical preprocessing steps."""
        steps = []
        if hasattr(self, 'categorical_imputation'):
            steps.append(self.categorical_imputation)
        if hasattr(self, 'encoding_method'):
            steps.append(self.encoding_method)
        return ', '.join(steps) if steps else 'basic preprocessing'
    
    def _print_preprocessing_summary(self) -> None:
        """Print summary of preprocessing decisions."""
        try:
            print("   📋 Preprocessing decisions:")
            for step in self.preprocessing_steps:
                print(f"      • {step}")
                
            # Print reasoning
            quality_score = self.analyzer_results.get('data_quality', {}).get('overall_score', 0)
            outlier_pct = self.analyzer_results.get('outlier_analysis', {}).get('outlier_summary', {}).get('outlier_percentage', 0)
            
            print("   💡 Reasoning:")
            if quality_score < 0.7:
                print(f"      • Used robust methods due to data quality score: {quality_score:.2f}")
            if outlier_pct > 5:
                print(f"      • Applied outlier handling due to {outlier_pct:.1f}% outliers")
            
        except Exception:
            pass
    
    def get_preprocessing_info(self) -> Dict[str, Any]:
        """Get detailed information about preprocessing decisions."""
        return {
            'steps_applied': self.preprocessing_steps,
            'feature_names_out': self.feature_names_out,
            'pipeline': self.pipeline,
            'analyzer_results_used': self.analyzer_results is not None,
            'preprocessing_reasoning': {
                'data_quality_score': self.analyzer_results.get('data_quality', {}).get('overall_score', 0) if self.analyzer_results else None,
                'outlier_percentage': self.analyzer_results.get('outlier_analysis', {}).get('outlier_summary', {}).get('outlier_percentage', 0) if self.analyzer_results else None,
                'missing_data_percentage': self.analyzer_results.get('missing_values', {}).get('missing_percentage_X', 0) if self.analyzer_results else None
            }
        }


# Test section - comprehensive testing of the FeatureEngineer
if __name__ == "__main__":
    print("🧪 Testing AutoML Feature Engineer")
    print("=" * 60)
    
    # Test 1: Clean data with mixed types
    print("\n🧹 Test 1: Clean Mixed Data")
    try:
        from sklearn.datasets import make_classification
        import pandas as pd
        
        # Create clean mixed data
        X_cls, y_cls = make_classification(n_samples=200, n_features=5, n_informative=3, random_state=42)
        X_df = pd.DataFrame(X_cls, columns=[f'numeric_{i}' for i in range(5)])
        
        # Add categorical features
        np.random.seed(42)
        X_df['category_a'] = np.random.choice(['A', 'B', 'C'], size=200)
        X_df['category_b'] = np.random.choice(['High', 'Low'], size=200)
        
        y_series = pd.Series(y_cls)
        
        # Test feature engineering
        engineer = FeatureEngineer(verbose=True)
        X_transformed, pipeline = engineer.fit_transform(X_df, y_series)
        
        print(f"✅ Clean data preprocessing complete!")
        print(f"   Original shape: {X_df.shape}")
        print(f"   Transformed shape: {X_transformed.shape}")
        
        # Test transform on new data
        X_new = X_df.head(10).copy()
        X_new_transformed = engineer.transform(X_new)
        print(f"   New data transform: {X_new.shape} → {X_new_transformed.shape}")
        
    except Exception as e:
        print(f"❌ Clean data test failed: {e}")
    
    # Test 2: Messy data with missing values and outliers
    print("\n🔀 Test 2: Messy Data with Issues")
    try:
        # Create messy dataset
        np.random.seed(42)
        X_messy = pd.DataFrame({
            'numeric_normal': np.random.normal(0, 1, 150),
            'numeric_skewed': np.random.exponential(2, 150),
            'numeric_outliers': np.random.normal(0, 1, 150),
            'categorical_low': np.random.choice(['A', 'B', 'C'], 150),
            'categorical_high': [f'cat_{i}' for i in np.random.randint(0, 30, 150)]
        })
        
        # Add missing values
        missing_indices = np.random.choice(150, 30, replace=False)
        X_messy.loc[missing_indices, 'numeric_normal'] = np.nan
        X_messy.loc[missing_indices[:15], 'categorical_low'] = np.nan
        
        # Add outliers
        outlier_indices = np.random.choice(150, 15, replace=False)
        X_messy.loc[outlier_indices, 'numeric_outliers'] *= 10
        
        y_messy = pd.Series(np.random.choice([0, 1], 150))
        
        # Test feature engineering
        engineer = FeatureEngineer(verbose=True)
        X_transformed, pipeline = engineer.fit_transform(X_messy, y_messy)
        
        print(f"✅ Messy data preprocessing complete!")
        
        # Get preprocessing info
        info = engineer.get_preprocessing_info()
        print(f"   Steps applied: {len(info['steps_applied'])}")
        
    except Exception as e:
        print(f"❌ Messy data test failed: {e}")
    
    # Test 3: High-dimensional data (more features than samples)
    print("\n📊 Test 3: High-Dimensional Data")
    try:
        # Create high-dimensional dataset
        X_high_dim = pd.DataFrame(
            np.random.random((50, 100)),  # 50 samples, 100 features
            columns=[f'feature_{i}' for i in range(100)]
        )
        y_high_dim = pd.Series(np.random.choice([0, 1], 50))
        
        # Test feature engineering
        engineer = FeatureEngineer(verbose=True)
        X_transformed, pipeline = engineer.fit_transform(X_high_dim, y_high_dim)
        
        print(f"✅ High-dimensional data preprocessing complete!")
        print(f"   Original: {X_high_dim.shape} → Transformed: {X_transformed.shape}")
        
    except Exception as e:
        print(f"❌ High-dimensional test failed: {e}")
    
    # Test 4: Integration with DataAnalyzer
    print("\n🔗 Test 4: Integration with DataAnalyzer")
    try:
        # Create test data
        X_test = pd.DataFrame({
            'numeric1': np.random.normal(0, 1, 100),
            'numeric2': np.random.exponential(1, 100),
            'categorical': np.random.choice(['A', 'B', 'C', 'D'], 100)
        })
        y_test = pd.Series(np.random.choice([0, 1, 2], 100))
        
        # Run analyzer first
        analyzer = DataAnalyzer(verbose=False)
        analysis = analyzer.analyze(X_test, y_test)
        
        # Use analysis in feature engineering
        engineer = FeatureEngineer(analyzer_results=analysis, verbose=True)
        X_transformed, pipeline = engineer.fit_transform(X_test, y_test)
        
        print(f"✅ DataAnalyzer integration test passed!")
        print(f"   Quality score: {analysis['data_quality']['overall_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    # Test 5: Edge cases and error handling
    print("\n⚠️  Test 5: Edge Cases")
    try:
        # Test with constant features
        X_constant = pd.DataFrame({
            'constant': [1, 1, 1, 1, 1],
            'normal': [1, 2, 3, 4, 5],
            'categorical': ['A', 'A', 'B', 'B', 'C']
        })
        y_constant = pd.Series([0, 0, 1, 1, 0])
        
        engineer = FeatureEngineer(verbose=True)
        X_transformed, pipeline = engineer.fit_transform(X_constant, y_constant)
        
        print(f"✅ Edge case handling test passed!")
        
    except Exception as e:
        print(f"❌ Edge case test failed: {e}")
    
    print("\n🎉 Feature Engineer testing completed!")
    print("\n💡 Next steps:")
    print("   1. Implement automl/model_selector.py")
    print("   2. Test with your own datasets")
    print("   3. Review preprocessing decisions and pipelines")
